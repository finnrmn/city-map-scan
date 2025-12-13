const video = document.getElementById('camera-video');
const canvas = document.getElementById('photo-canvas');

const takePhotoBtn = document.getElementById('take-photo-btn');
const retakePhotoBtn = document.getElementById('retake-photo-btn');
const uploadImageBtn = document.getElementById('upload-image-btn');
const sendImageBtn = document.getElementById('send-image-btn');
const uploadInput = document.getElementById('upload-input');
const cityNameAnimation = document.getElementById('city-name');
const loadingAnimation = document.getElementById('loading-animation');

let stream = null;
let photoTaken = false;
let imgData = null;
let recognizedCity = "";

// --- Section 1 Kamera --- //

// --- Section‑1‑Buttons gruppieren & sperren/freigeben ----------------------
const section1Buttons = [takePhotoBtn, retakePhotoBtn, uploadImageBtn, sendImageBtn];

function toggleSection1Buttons(isDisabled) {
    section1Buttons.forEach(btn => btn.disabled = isDisabled);
}

//-------------------------------------------------------------------
async function startCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({
            video: {facingMode: {exact: "environment"}}
        });

        video.srcObject = stream;
        video.play();
        video.style.display = 'block';
        canvas.style.display = 'none';
    } catch (e) {
        video.style.display = 'none';
        canvas.style.display = 'block';
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#c2c7ce';
        ctx.font = '32px Inter,sans-serif';
        ctx.fillStyle = '#fff';
        ctx.fillText('No camera available', 50, 100);
    }
}

async function showPhoto() {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    video.style.display = 'none';
    canvas.style.display = 'block';
    imgData = await resizeImage(canvas.toDataURL('image/jpeg'), 2000, 0.8);
    photoTaken = true;
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }
    updateButtonStates();
}

function uploadPhoto(file) {
    const reader = new FileReader();
    reader.onload = function (e) {
        const img = new Image();
        img.onload = async function () {
            canvas.width = img.width;
            canvas.height = img.height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, img.width, img.height);
            canvas.style.display = 'block';
            video.style.display = 'none';
            imgData = await resizeImage(reader.result, 2000, 0.8);

            photoTaken = true;
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
                stream = null;
            }
            updateButtonStates();
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

function retakePhoto() {
    imgData = null;
    canvas.style.display = 'none';
    video.style.display = 'block';
    photoTaken = false;
    if (!stream) startCamera();
    updateButtonStates();
    document.getElementById('section-pois').style.display = 'none';
    document.getElementById('section-map').style.display = 'none';
    cityNameAnimation.classList.remove('visible');
}

function updateButtonStates() {
    if (!photoTaken) {
        // Zustand: KEIN Bild vorhanden
        takePhotoBtn.style.display = 'flex';
        retakePhotoBtn.style.display = 'none';
        uploadImageBtn.style.display = 'flex';
        sendImageBtn.style.display = 'none';
    } else {
        // Zustand: Bild vorhanden (egal ob aufgenommen oder hochgeladen)
        takePhotoBtn.style.display = 'none';
        retakePhotoBtn.style.display = 'flex';
        uploadImageBtn.style.display = 'none';
        sendImageBtn.style.display = 'flex';
    }
}

// EVENTS
takePhotoBtn.addEventListener('click', showPhoto);
retakePhotoBtn.addEventListener('click', retakePhoto);

uploadImageBtn.addEventListener('click', () => uploadInput.click());
uploadInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file && file.type.startsWith('image/')) {
        uploadPhoto(file);
    }
});

sendImageBtn.addEventListener('click', async () => {
    document.getElementById('section-pois').style.display = 'none';
    document.getElementById('section-map').style.display = 'none';
    if (!imgData) {
        alert("Bitte zuerst ein Bild aufnehmen oder hochladen.");
        return;
    }

    toggleSection1Buttons(true);
    document.getElementById('loading-animation').style.display = "flex"

    const response = await fetch('/upload', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: new URLSearchParams({photo: imgData})
    });
    if (!response.ok) throw new Error('Upload fehlgeschlagen');
    const data = await response.json();

    let city = data.city;
    console.log('city:', city);
    let city_backup = data.city_backup;
    let city_print = city

    document.getElementById('loading-animation').style.display = "none";
    //document.getElementById("pois-loader-wrapper").style.display = 'block';
    document.getElementById('pois-loading-section').style.display = 'flex';

    toggleSection1Buttons(false);

    if (city === "Unklar") {
        if (!city_backup || city_backup.length === 0) {
            city = "Unklar";
            city_print = "Unklar";
        } else if (city_backup.length > 0) {
            city = city_backup[0];
            city_print = city_backup.join(",") + " (nicht eindeutig)";
        }

    }

    recognizedCity = city;
    cityNameAnimation.textContent = city_print
    cityNameAnimation.classList.add('visible');
    cityDetected(city);
    setTimeout(() => {
        cityNameAnimation.classList.remove('visible');
    }, 3000);
});

window.addEventListener('DOMContentLoaded', () => {
    startCamera();
    updateButtonStates();
});

async function cityDetected(city) {
    await loadPoisForCity(city);
}

// -----------------------------------------------
//  IMAGE DOWNSCALE  (max 2k px Kante)
// -----------------------------------------------
async function resizeImage(dataUrl, maxSize = 2000, quality = 0.8) {
    return new Promise((resolve) => {
        const img = new Image();
        img.onload = () => {
            let {width, height} = img;

            // nur verkleinern, nie vergrößern
            if (width > maxSize || height > maxSize) {
                if (width > height) {
                    height = Math.round(height * (maxSize / width));
                    width = maxSize;
                } else {
                    width = Math.round(width * (maxSize / height));
                    height = maxSize;
                }
            }

            const canvas = document.createElement('canvas');
            canvas.width = width;
            canvas.height = height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, width, height);

            // JPEG Qualität 0.8 ≈ 80 %
            resolve(canvas.toDataURL('image/jpeg', quality));
        };
        img.src = dataUrl;
    });
}

// ------------------ Section 2: POIs Cards -------------------

async function loadPoisForCity(city) {
    try {
        const response = await fetch(`/api/pois?city=${encodeURIComponent(city)}`);
        if (!response.ok) throw new Error("Keine POI-Daten gefunden");
        const data = await response.json();
        recognizedCity = data.city_name || city || recognizedCity;
        console.log(data.pois_category);
        updatePOISection(data);
    } catch (error) {
        console.error(error);
        const data = null
        updatePOISection(data);
    }
}

function updatePOISection(data) {
    if (!data) {
        alert("POI-Section render nicht möglich - Keine Daten gefunden!")
        return
    }
    document.getElementById("pois-loading-section").style.display = "none";
    document.getElementById('section-pois').style.display = 'flex';
    document.getElementById('section-map').style.display = 'flex';
    const cityName = data.city_name || recognizedCity || "";
    const categories = data.pois_category || {};
    renderCardList('pois-cards', categories.pois || []);
    renderCardList('fun-cards', categories.fun || []);
    renderCardList('restaurants-cards', categories.restaurants || []);
    document.getElementById('pois-headline').textContent = `Sehenswürdigkeiten in ${cityName}`;
    document.getElementById('fun-headline').textContent = `Aktivitäten & Spaß in ${cityName}`;
    document.getElementById('restaurants-headline').textContent = `Restaurants in ${cityName}`;
    updateMapSection(cityName, data.city_iframe);
}



function renderCardList(containerId, items) {
    const cardList = document.getElementById(containerId);
    cardList.innerHTML = "";

    items.forEach(item => {
        const card = document.createElement('div');
        card.classList.add('poi-card');
        card.style.backgroundImage = `linear-gradient(rgba(0,0,0,.50), rgba(0,0,0,.40)),url('${item.photo_url || ''}')`;
        card.style.backgroundSize = 'cover';
        card.style.backgroundPosition = 'center';
        card.innerHTML = `
          <div class="poi-title">${item.name || ''}</div>
          <div class="poi-desc">${item.beschreibung || ''}</div>
        `;


        if (item.iframe_link) {
            card.style.cursor = "pointer";
            attachSmartClick(card, item.iframe_link, item.name);
        } else {
            card.style.opacity = "0.5";
        }

        cardList.appendChild(card);
    });
}

// ---------------- Helper: Klick vs. Swipe -------------------
function attachSmartClick(cardElem, iframeLink, poiName) {
    let downX = 0, downY = 0;

    // Pointerdown – Startposition merken
    cardElem.addEventListener('pointerdown', ev => {
        downX = ev.clientX;
        downY = ev.clientY;
    }, {passive: true});

    // Pointerup – Distanz auswerten
    cardElem.addEventListener('pointerup', ev => {
        const distX = Math.abs(ev.clientX - downX);
        const distY = Math.abs(ev.clientY - downY);

        // < 12 px Gesamtbewegung ⇒ echter Klick
        if (distX + distY < 12) {
            setMapHeadline(poiName);
            setMapIframeSrc(iframeLink);
        }
        // sonst war’s ein Swipe → nichts tun
    });
}

// ------------------ Section 3: Map ------------------------
function updateMapSection(city_name, iframe_link) {
    document.getElementById('map-headline').textContent = `${city_name} Map`;
    const mapIframe = document.getElementById('map-img');
    mapIframe.style.display = 'flex';
    mapIframe.src = iframe_link;
}

function setMapHeadline(poi_name) {
    document.getElementById('map-headline').textContent = `${recognizedCity} Map - ${poi_name}`;
}

function setMapIframeSrc(iframeLink) {
    const mapIframe = document.getElementById('map-img');
    if (mapIframe) {
        mapIframe.src = iframeLink;
    }
}

