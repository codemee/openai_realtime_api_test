let mediaStream = null;
let isStreamActive = false;

document.addEventListener('DOMContentLoaded', function() {
    const actionButton = document.getElementById('actionButton');
    updateButtonState(false);

    actionButton.addEventListener('click', async function() {
        if (!isStreamActive) {
            try {
                mediaStream = await navigator.mediaDevices.getUserMedia({
                    audio: true
                });
                isStreamActive = true;
                updateButtonState(true);
                appendStatus('麥克風已開啟');
                
                // 建立或更新 WebRTC 連線
                await initWebRTC(mediaStream);
            } catch (error) {
                console.error('無法取得麥克風存取權限:', error);
                appendStatus('無法取得麥克風存取權限');
            }
        } else {
            // 關閉麥克風
            if (mediaStream) {
                mediaStream.getTracks().forEach(track => track.stop());
                mediaStream = null;
            }
            isStreamActive = false;
            updateButtonState(false);
            appendStatus('麥克風已關閉');
        }
    });
});

// 更新按鈕狀態和文字
function updateButtonState(isActive) {
    const actionButton = document.getElementById('actionButton');
    if (isActive) {
        actionButton.textContent = '關閉麥克風';
        actionButton.classList.remove('btn-primary');
        actionButton.classList.add('btn-danger');
    } else {
        actionButton.textContent = '開啟麥克風';
        actionButton.classList.remove('btn-danger');
        actionButton.classList.add('btn-primary');
    }
}

// 在輸出區域顯示新的一行文字
function appendToOutput(text) {
    const outputArea = document.getElementById('outputArea');
    outputArea.innerHTML += text + '<br/>';
}

// 清除狀態標籤內容
function clearStatus() {
    const statusLabel = document.getElementById('statusLabel');
    statusLabel.textContent = '';
}

// 在狀態標籤尾端添加文字
function appendStatus(text) {
    const statusLabel = document.getElementById('statusLabel');
    statusLabel.textContent += text;
}

async function initWebRTC(stream) {
    // 取得臨時的 API 金鑰
    const response = await fetch("/key");
    const EPHEMERAL_KEY = await response.text();
    
    appendStatus('正在初始化 WebRTC...');
  
    // 建立 WebRTC 連線物件
    const pc = new RTCPeerConnection();
  
    // 建立播放語音的元素
    const audioEl = document.createElement("audio");
    audioEl.autoplay = true;
    pc.ontrack = e => audioEl.srcObject = e.streams[0];
  
    // 加入麥克風音軌
    pc.addTrack(stream.getTracks()[0]);
    appendStatus('音訊串流已就緒 ');
  
    // 設定傳遞 Realtime API 事件的資料通道
    const dc = pc.createDataChannel("oai-events");
    dc.addEventListener("message", (e) => {
        const event = JSON.parse(e.data);
        appendToOutput(event.type);

        if (event.type === "conversation.item.created") {
            clearStatus();
        }
        else if (event.type === "response.audio_transcript.delta") {
            appendStatus(event.delta);
        }
    });
  
    // Start the session using the Session Description Protocol (SDP)
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
  
    const baseUrl = "https://api.openai.com/v1/realtime";
    const model = "gpt-4o-realtime-preview";
    const sdpResponse = await fetch(`${baseUrl}?model=${model}`, {
        method: "POST",
        body: offer.sdp,
        headers: {
            Authorization: `Bearer ${EPHEMERAL_KEY}`,
            "Content-Type": "application/sdp"
        },
    });
  
    const answer = {
        type: "answer",
        sdp: await sdpResponse.text(),
    };
    await pc.setRemoteDescription(answer);
}