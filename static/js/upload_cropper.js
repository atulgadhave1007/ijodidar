let cropper, fileSelected = false;

// Detect whether it's profile page (circular crop) or gallery page (free crop)
const isProfilePage = document.getElementById('clickablePreview') !== null;

const input = document.getElementById('imageInput'),
      cropImg = document.getElementById('cropImage'),
      cropCont = document.getElementById('cropContainer'),
      cropTools = document.getElementById('cropToolbar'),
      uploadBtn = document.getElementById('uploadBtn'),
      modal = document.getElementById('uploadModal'),
      prWrap = document.getElementById('uploadProgressWrapper'),
      prBar = document.getElementById('uploadProgressBar'),
      previewImage = document.getElementById('previewImage'),
      initialsContainer = document.getElementById('previewImageContainer'),
      dropArea = document.getElementById('dropArea');

// Click to upload (only for profile page)
document.getElementById('clickablePreview')?.addEventListener('click', () => input?.click());

// Drag & Drop
dropArea?.addEventListener('dragover', e => {
  e.preventDefault();
  dropArea.classList.add('dragover');
});
dropArea?.addEventListener('dragleave', () => dropArea.classList.remove('dragover'));
dropArea?.addEventListener('drop', e => {
  e.preventDefault();
  dropArea.classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file) handleFile(file);
});

// File input
input?.addEventListener('change', e => {
  const file = e.target.files[0];
  if (file) handleFile(file);
});

function handleFile(file) {
  const maxSize = 5 * 1024 * 1024;
  if (file.size > maxSize) {
    alert("Image exceeds 5MB limit.");
    input.value = '';
    return;
  }

  fileSelected = true;
  const reader = new FileReader();
  reader.onload = () => {
    cropImg.src = reader.result;

    // 👇 Hide previous profile image or initials preview
    if (previewImage) {
      previewImage.style.display = 'none';  // Hide old image preview
      previewImage.src = '';                // Clear it completely
    }
    if (initialsContainer) {
      initialsContainer.style.display = 'none'; // Hide initials container
    }

    // 👇 Show crop container and tools
    cropCont.classList.remove('d-none');
    cropTools.classList.remove('d-none');

    // 👇 Destroy previous cropper and re-init
    cropper?.destroy();
    cropper = new Cropper(cropImg, {
      aspectRatio: isProfilePage ? 1 : NaN,
      viewMode: 1,
      dragMode: 'move',
      autoCropArea: 1,
      cropBoxResizable: !isProfilePage,
      cropBoxMovable: !isProfilePage,
      background: false,
      guides: false,
      highlight: false,
      center: true,
      ready() {
        if (isProfilePage) {
          document.querySelector('.cropper-crop-box')?.style.setProperty('border-radius', '50%');
          document.querySelector('.cropper-face')?.style.setProperty('border-radius', '50%');
        }
      }
    });
  };
  reader.readAsDataURL(file);
}

uploadBtn?.addEventListener('click', () => {
  if (!fileSelected || !cropper) return alert("Please select and crop an image first.");

  const cropData = cropper.getData(true);
  const imageData = cropper.getImageData();

  let exportWidth = Math.min(Math.floor(cropData.width), 1200);
  let exportHeight = Math.min(Math.floor(cropData.height), 1200);

  if (isProfilePage) {
    const side = Math.min(exportWidth, exportHeight);
    exportWidth = exportHeight = side;
  }

  cropper.getCroppedCanvas({
    width: exportWidth,
    height: exportHeight,
    imageSmoothingEnabled: true,
    imageSmoothingQuality: 'high',
  }).toBlob(blob => {
    const formData = new FormData();
    formData.append('image', blob, 'upload.jpg');
    formData.append('is_primary', isProfilePage ? 'true' : 'false');

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/upload_image');

    xhr.upload.onprogress = e => {
      if (e.lengthComputable) {
        const percent = Math.round((e.loaded / e.total) * 100);
        prBar.style.width = `${percent}%`;
        prBar.textContent = `${percent}%`;
        prWrap.classList.remove('d-none');
      }
    };

    xhr.onload = () => {
      bootstrap.Modal.getInstance(modal)?.hide();
      if (xhr.status === 200) {
        const successToast = document.getElementById('uploadSuccessToast');
        if (successToast) {
          new bootstrap.Toast(successToast).show();
          successToast.addEventListener('hidden.bs.toast', () => location.reload());
        } else {
          location.reload();
        }
      } else {
        const failToast = document.getElementById('uploadFailToast');
        failToast ? new bootstrap.Toast(failToast).show() : alert("Upload failed.");
      }
    };

    xhr.onerror = () => {
      bootstrap.Modal.getInstance(modal)?.hide();
      const failToast = document.getElementById('uploadFailToast');
      failToast ? new bootstrap.Toast(failToast).show() : alert("Upload failed.");
    };

    xhr.send(formData);
  }, 'image/jpeg', 0.92);
});

modal?.addEventListener('hidden.bs.modal', () => {
  cropper?.destroy(); cropper = null;
  fileSelected = false;
  input.value = '';
  cropCont.classList.add('d-none');
  cropTools.classList.add('d-none');
  prWrap.classList.add('d-none');
  prBar.style.width = '0%';
  prBar.textContent = '0%';
  previewImage && (previewImage.src = '', previewImage.style.display = 'none');
  initialsContainer && (initialsContainer.style.display = 'flex');
});

function zoomCrop(v) { cropper?.zoom(v); }
function resetCrop() { cropper?.reset(); }
