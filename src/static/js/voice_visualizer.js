const blob = document.getElementById("voiceBlob");
let userAnalyser = null;
let aiAnalyser = null;
let userDataArray = null;
let aiDataArray = null;

function startBlobAnimation() {
    function animate() {
        let totalVolume = 0;
        let count = 0;

        if (userAnalyser && userDataArray) {
            userAnalyser.getByteFrequencyData(userDataArray);
            const sum = userDataArray.reduce((a, b) => a + b, 0);
            totalVolume += sum / userDataArray.length;
            count++;
        }

        if (aiAnalyser && aiDataArray) {
            aiAnalyser.getByteFrequencyData(aiDataArray);
            const sum = aiDataArray.reduce((a, b) => a + b, 0);
            totalVolume += sum / aiDataArray.length;
            count++;
        }

        const average = count > 0 ? totalVolume / count : 0;
        const scale = 1 + average / 100;

        if (blob) {
            blob.style.transform = `scale(${scale})`;
        }

        requestAnimationFrame(animate);
    }

    animate();
}

// User mic input
navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioCtx.createMediaStreamSource(stream);
    userAnalyser = audioCtx.createAnalyser();
    userAnalyser.fftSize = 256;
    userDataArray = new Uint8Array(userAnalyser.frequencyBinCount);
    source.connect(userAnalyser);

    startBlobAnimation();  // Start after user analyser is ready
}).catch(err => {
    console.error('Microphone access denied or error', err);
});

// This function should be called from app.js when AI audio is available
function attachAIAudio(stream) {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioCtx.createMediaStreamSource(stream);
    aiAnalyser = audioCtx.createAnalyser();
    aiAnalyser.fftSize = 256;
    aiDataArray = new Uint8Array(aiAnalyser.frequencyBinCount);
    source.connect(aiAnalyser);
}

// Make the function globally accessible
window.attachAIAudio = attachAIAudio;