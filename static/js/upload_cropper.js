// upload_cropper.js — image crop + S3 upload via form POST
let cropper = null;

document.addEventListener('DOMContentLoaded', () => {
  const input       = document.getElementById('imageInput');
  const cropImg     = document.getElementById('cropImage');
  const cropCont    = document.getElementById('cropContainer');
  const cropToolbar = document.getElementById('cropToolbar');
  const uploadBtn   = document.getElementById('uploadBtn');
  const isPrimary   = document.getElementById('isPrimary');
  const progressWrap = document.getElementById('uploadProgressWrapper');
  const progressBar  = document.getElementById('uploadProgressBar');

  if (!input) return;

  input.addEventListener('change', e => {
    const file = e.target.files[0];
    if (!file) return;
    if (!['image/jpeg','image/png'].includes(file.type)) {
      alert('Only JPG or PNG images are allowed.'); input.value = ''; return;
    }
    if (file.size > 2 * 1024 * 1024) {
      alert('File must be under 2 MB.'); input.value = ''; return;
    }
    const reader = new FileReader();
    reader.onload = ev => {
      cropImg.src = ev.target.result;
      cropCont.classList.remove('d-none');
      cropToolbar.classList.remove('d-none');
      if (cropper) cropper.destroy();
      cropper = new Cropper(cropImg, { aspectRatio: 1, viewMode: 1, autoCropArea: .9 });
    };
    reader.readAsDataURL(file);
  });

  uploadBtn && uploadBtn.addEventListener('click', () => {
    if (!cropper) { alert('Please select an image first.'); return; }
    cropper.getCroppedCanvas({ width: 800, height: 800 }).toBlob(blob => {
      const fd = new FormData();
      fd.append('image', blob, 'profile.jpg');
      if (isPrimary && isPrimary.checked) fd.append('is_primary', '1');

      progressWrap && progressWrap.classList.remove('d-none');
      uploadBtn.disabled = true;

      const xhr = new XMLHttpRequest();
      xhr.open('POST', '/upload_image');
      xhr.upload.onprogress = e => {
        if (e.lengthComputable && progressBar) {
          progressBar.style.width = Math.round(e.loaded / e.total * 100) + '%';
        }
      };
      xhr.onload = () => {
        if (xhr.status < 400) { window.location.reload(); }
        else { alert('Upload failed. Please try again.'); uploadBtn.disabled = false; }
      };
      xhr.onerror = () => { alert('Network error.'); uploadBtn.disabled = false; };
      xhr.send(fd);
    }, 'image/jpeg', 0.88);
  });
});

function zoomCrop(ratio) { if (cropper) cropper.zoom(ratio); }
function resetCrop()     { if (cropper) cropper.reset(); }
