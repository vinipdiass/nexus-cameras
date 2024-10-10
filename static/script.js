const video = document.getElementById('video');

function startVideo() {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                video.srcObject = stream;
                video.play();
                sendFrames();
            })
            .catch(err => {
                console.error("Erro ao acessar a webcam: ", err);
                alert("Erro ao acessar a webcam. Verifique se você concedeu permissão.");
            });
    } else {
        alert("Navegador não suporta acesso à webcam.");
    }
}

function sendFrames() {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    const FPS = 10; // Frames per second

    setInterval(() => {
        if (video.readyState === video.HAVE_ENOUGH_DATA) {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            context.drawImage(video, 0, 0, canvas.width, canvas.height);

            canvas.toBlob(blob => {
                fetch('http://localhost:8000/upload_frame', { // Certifique-se de que a URL está correta
                    method: 'POST',
                    body: blob
                }).catch(err => {
                    console.error("Erro ao enviar o frame: ", err);
                });
            }, 'image/jpeg');
        }
    }, 1000 / FPS);
}

startVideo();
