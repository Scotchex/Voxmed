// Global variables
let peerConnection = null;
let dataChannel = null;
let isConnected = false;

// DOM elements
const ringBox = document.getElementById('ringBox');
const callButton = document.getElementById('callButton');
const endCallBtn = document.getElementById('endCallBtn');
const callStatus = document.querySelector('.call-status');

// Start the call
async function startCall() {
    ringBox.style.display = 'block';
    callStatus.textContent = 'Connecting...';
    await initOpenAIRealtime();
}

// Initialize OpenAI Realtime connection
async function initOpenAIRealtime() {
    try {
        const tokenResponse = await fetch("/session");
        const data = await tokenResponse.json();
        const EPHEMERAL_KEY = data.client_secret.value;

        peerConnection = new RTCPeerConnection();

        peerConnection.onconnectionstatechange = () => {
            console.log("Connection state:", peerConnection.connectionState);
            if (peerConnection.connectionState === 'connected') {
                isConnected = true;
                callStatus.textContent = 'Connected';
                endCallBtn.style.display = 'block';
            }
        };

        const audioElement = document.createElement("audio");
        audioElement.autoplay = true;
        peerConnection.ontrack = event => {
            const remoteStream = event.streams[0];
            audioElement.srcObject = remoteStream;
            if (window.attachAIAudio) {
                window.attachAIAudio(remoteStream);
            }
        };

        const mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        peerConnection.addTrack(mediaStream.getTracks()[0]);

        dataChannel = peerConnection.createDataChannel('response');

        dataChannel.addEventListener('open', () => {
            console.log('Data channel opened');
            configureData();
        });

        dataChannel.addEventListener('message', async (ev) => {
            try {
                const msg = JSON.parse(ev.data);
                console.log(msg);

                const timestamp = new Date().toISOString();

                // Assistant message
                if (
                    msg.type === 'response.output_item.done' &&
                    msg.item?.role === 'assistant' &&
                    msg.item?.type === 'message'
                ) {
                    const contentArray = msg.item.content;
                    const transcriptObj = contentArray.find(c => c.type === 'audio' && c.transcript);

                    if (transcriptObj) {
                        const text = transcriptObj.transcript;
                        console.log("Assistant:", text);

                        fetch("/store_response", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({
                                role: "assistant",
                                message: text,
                                timestamp: timestamp
                            })
                        });
                    }
                }

                // User message
                if (
                    msg.type === 'conversation.item.input_audio_transcription.completed' &&
                    msg.transcript
                ) {
                    console.log("User:", msg.transcript);
                    fetch("/store_response", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            role: "user",
                            message: msg.transcript,
                            timestamp: timestamp
                        })
                    });
                }

                // Handle function call output
                if (msg.type === 'response.function_call_arguments.done') {
                    const fn = fns[msg.name];
                    if (fn) {
                        const args = JSON.parse(msg.arguments);
                        const result = await fn(args);
                        const event = {
                            type: 'conversation.item.create',
                            item: {
                                type: 'function_call_output',
                                call_id: msg.call_id,
                                output: JSON.stringify(result)
                            }
                        };
                        dataChannel.send(JSON.stringify(event));
                    }
                }
            } catch (error) {
                console.error('Message handling error:', error);
            }
        });

        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);

        const apiUrl = "https://api.openai.com/v1/realtime";
        const model = "gpt-4o-mini-realtime-preview-2024-12-17";

        const sdpResponse = await fetch(`${apiUrl}?model=${model}`, {
            method: "POST",
            body: offer.sdp,
            headers: {
                Authorization: `Bearer ${EPHEMERAL_KEY}`,
                "Content-Type": "application/sdp"
            }
        });

        const answer = {
            type: "answer",
            sdp: await sdpResponse.text()
        };
        await peerConnection.setRemoteDescription(answer);

    } catch (error) {
        console.error("Error initializing realtime:", error);
        endCall();
    }
}

// Send session update config
function configureData() {
    console.log('Configuring data channel');
    const event = {
        type: 'session.update',
        session: {
            modalities: ['text', 'audio'],
            input_audio_transcription: {
                model: 'gpt-4o-transcribe'
            }
        }
    };
    dataChannel.send(JSON.stringify(event));
}

// End the call
function endCall() {
    if (peerConnection) {
        peerConnection.close();
        peerConnection = null;
    }

    ringBox.style.display = 'none';
    callButton.style.display = 'block';
    endCallBtn.style.display = 'none';
    callStatus.textContent = 'Ready to talk';
    isConnected = false;

    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        mainContent.style.display = 'flex';
    }
    //sending the llm stuff//
    fetch("/end_call_analysis", {
        method: "POST"
    })
    .then(res => res.json())
    .then(data => {
        console.log("Analysis complete!", data);
    })
    .catch(error => {
        console.error("Failed to analyze session!", error);
    })
}

// Event listeners
callButton.addEventListener('click', startCall);
endCallBtn.addEventListener('click', endCall);
