// Hoşgeldiniz animasyonu için metin ve ayarlar
const welcomeText = "Hoş Geldin Bremın";
const typingText = document.querySelector('.typing-text');
let charIndex = 0;
const typingSpeed = 30; // Daha hızlı yazma için düşük değer

// Yazı animasyonu fonksiyonu
function typeText() {
    if (charIndex < welcomeText.length) {
        typingText.textContent += welcomeText.charAt(charIndex);
        charIndex++;
        setTimeout(typeText, typingSpeed);
    } else {
        setTimeout(hideWelcomeScreen, 800);
    }
}

// Hoşgeldiniz ekranını gizleme
function hideWelcomeScreen() {
    const welcomeScreen = document.querySelector('.welcome-screen');
    const mainContent = document.querySelector('.main-content');
    
    welcomeScreen.style.opacity = '0';
    
    setTimeout(() => {
        welcomeScreen.style.display = 'none';
        mainContent.style.display = 'block';
        initializeMainContent();
        createBubbles(); // Arka plan animasyonlarını başlat
    }, 500);
}

// Ana içeriği başlatma
function initializeMainContent() {
    const elements = [
        '.hero-title',
        '.hero-subtitle',
        '.download-card',
        '.features'
    ];

    elements.forEach((element, index) => {
        document.querySelector(element).style.animation = 
            `fadeInUp 0.8s ${index * 0.2}s forwards`;
    });
}

// Arka plan animasyonları için kabarcıklar oluşturma
function createBubbles() {
    const bubblesContainer = document.querySelector('.bubbles');
    const bubbleCount = 15;

    for (let i = 0; i < bubbleCount; i++) {
        const bubble = document.createElement('div');
        bubble.className = 'bubble';
        
        // Rastgele boyut ve pozisyon
        const size = Math.random() * 60 + 20;
        bubble.style.width = `${size}px`;
        bubble.style.height = `${size}px`;
        bubble.style.left = `${Math.random() * 100}%`;
        bubble.style.top = `${Math.random() * 100}%`;
        
        // Rastgele animasyon süresi ve gecikme
        bubble.style.animationDuration = `${Math.random() * 2 + 3}s`;
        bubble.style.animationDelay = `${Math.random() * 2}s`;
        
        bubblesContainer.appendChild(bubble);
    }
}

// URL işleme ve platform algılama
document.querySelector('.url-input').addEventListener('input', function(e) {
    const url = e.target.value.trim();
    const formatButtons = document.querySelector('.format-buttons');
    const platforms = document.querySelectorAll('.platform-icon');
    
    platforms.forEach(icon => icon.classList.remove('active'));
    
    if (url) {
        formatButtons.classList.add('show');
        if (url.includes('youtube.com') || url.includes('youtu.be')) {
            document.querySelector('.youtube').classList.add('active');
            showVideoPreview(url);
        } else if (url.includes('tiktok.com')) {
            document.querySelector('.tiktok').classList.add('active');
        } else if (url.includes('instagram.com')) {
            document.querySelector('.instagram').classList.add('active');
        } else if (url.includes('twitter.com') || url.includes('x.com')) {
            document.querySelector('.twitter').classList.add('active');
        }
    } else {
        formatButtons.classList.remove('show');
        hideVideoPreview();
    }
});

// Yapıştır butonu işlevselliği
document.querySelector('.paste-btn').addEventListener('click', async () => {
    try {
        const text = await navigator.clipboard.readText();
        const input = document.querySelector('.url-input');
        const pasteBtn = document.querySelector('.paste-btn');
        
        input.value = text;
        input.dispatchEvent(new Event('input'));
        
        // Butonu yeşil yap
        pasteBtn.classList.add('active');
        setTimeout(() => {
            pasteBtn.classList.remove('active');
        }, 2000);
    } catch (err) {
        console.error('Panoya erişilemedi:', err);
    }
});

// Video önizleme fonksiyonları
function showVideoPreview(url) {
    const videoId = extractYoutubeId(url);
    if (videoId) {
        const previewContainer = document.getElementById('videoPreview');
        previewContainer.innerHTML = `
            <iframe 
                width="100%" 
                height="315" 
                src="https://www.youtube.com/embed/${videoId}" 
                frameborder="0" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowfullscreen>
            </iframe>
        `;
        previewContainer.style.display = 'block';
    }
}

function hideVideoPreview() {
    const previewContainer = document.getElementById('videoPreview');
    previewContainer.style.display = 'none';
    previewContainer.innerHTML = '';
}

function extractYoutubeId(url) {
    const regExp = /^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[7].length == 11) ? match[7] : false;
}

// İndirme fonksiyonu
function downloadVideo(format) {
    const url = document.querySelector('.url-input').value.trim();
    
    if (!url) {
        showNotification('Lütfen bir video linki girin!', 'error');
        return;
    }

    showLoader();

    fetch('/download', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            url: url,
            format: format
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = data.download_url;
            setTimeout(hideLoader, 2000);
        } else {
            showNotification('İndirme hatası: ' + data.error, 'error');
            hideLoader();
        }
    })
    .catch(error => {
        showNotification('Bir hata oluştu: ' + error, 'error');
        hideLoader();
    });
}

// Loader kontrolü
function showLoader() {
    document.getElementById('loader').style.display = 'flex';
}

function hideLoader() {
    document.getElementById('loader').style.display = 'none';
}

// Bildirim fonksiyonu (sadece hata bildirimleri için)
function showNotification(message, type) {
    if (type === 'error') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }
}

// Sayfa yüklendiğinde
window.onload = () => {
    typeText();
    
    // URL parametresi varsa otomatik yapıştır
    const urlParams = new URLSearchParams(window.location.search);
    const videoUrl = urlParams.get('url');
    if (videoUrl) {
        document.querySelector('.url-input').value = videoUrl;
        document.querySelector('.url-input').dispatchEvent(new Event('input'));
    }
};