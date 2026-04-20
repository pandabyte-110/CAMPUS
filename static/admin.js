const imageInput = document.getElementById("imageInput");
const preview = document.getElementById("preview");
const imageResizeInfo = document.getElementById("imageResizeInfo");
const toggleGalleryBtn = document.getElementById("toggleGalleryBtn");
const adminGallery = document.getElementById("adminGallery");
const thumbnailButtons = document.querySelectorAll(".thumbnail-button");
const imageModal = document.getElementById("imageModal");
const modalImage = document.getElementById("modalImage");
const modalImageTitle = document.getElementById("modalImageTitle");
const closeImageModal = document.getElementById("closeImageModal");

const MAX_IMAGE_WIDTH = 1280;
const MAX_IMAGE_HEIGHT = 1280;
const IMAGE_QUALITY = 0.88;

const formatBytes = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
};

const loadImage = (file) => new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("Could not load image for resizing."));
    image.src = URL.createObjectURL(file);
});

const resizeImageFile = async (file) => {
    const image = await loadImage(file);
    const widthScale = MAX_IMAGE_WIDTH / image.width;
    const heightScale = MAX_IMAGE_HEIGHT / image.height;
    const scale = Math.min(1, widthScale, heightScale);

    const targetWidth = Math.max(1, Math.round(image.width * scale));
    const targetHeight = Math.max(1, Math.round(image.height * scale));

    const canvas = document.createElement("canvas");
    canvas.width = targetWidth;
    canvas.height = targetHeight;

    const context = canvas.getContext("2d");
    context.drawImage(image, 0, 0, targetWidth, targetHeight);

    const preferredType = ["image/jpeg", "image/png", "image/webp"].includes(file.type)
        ? file.type
        : "image/jpeg";

    const blob = await new Promise((resolve, reject) => {
        canvas.toBlob((result) => {
            if (!result) {
                reject(new Error("Could not generate resized image."));
                return;
            }
            resolve(result);
        }, preferredType, IMAGE_QUALITY);
    });

    URL.revokeObjectURL(image.src);

    const extension = preferredType === "image/png" ? "png" : preferredType === "image/webp" ? "webp" : "jpg";
    const safeName = file.name.replace(/\.[^.]+$/, "");
    const resizedFile = new File([blob], `${safeName}_resized.${extension}`, { type: preferredType });

    return {
        resizedFile,
        originalWidth: image.width,
        originalHeight: image.height,
        targetWidth,
        targetHeight
    };
};

if (imageInput && preview) {
    imageInput.addEventListener("change", async (event) => {
        const file = event.target.files[0];

        if (!file) {
            preview.style.display = "none";
            if (imageResizeInfo) {
                imageResizeInfo.textContent = "Selected image will be resized automatically before upload for better performance.";
            }
            return;
        }

        if (!file.type.startsWith("image/")) {
            if (imageResizeInfo) {
                imageResizeInfo.textContent = "Please select a valid image file.";
            }
            return;
        }

        try {
            const { resizedFile, originalWidth, originalHeight, targetWidth, targetHeight } = await resizeImageFile(file);

            const transfer = new DataTransfer();
            transfer.items.add(resizedFile);
            imageInput.files = transfer.files;

            preview.src = URL.createObjectURL(resizedFile);
            preview.style.display = "block";

            if (imageResizeInfo) {
                imageResizeInfo.textContent = `Resized ${originalWidth}x${originalHeight} (${formatBytes(file.size)}) to ${targetWidth}x${targetHeight} (${formatBytes(resizedFile.size)}).`;
            }
        } catch (error) {
            if (imageResizeInfo) {
                imageResizeInfo.textContent = "Image resize failed. Original file will be uploaded.";
            }

            preview.src = URL.createObjectURL(file);
            preview.style.display = "block";
        }
    });
}

if (toggleGalleryBtn && adminGallery) {
    toggleGalleryBtn.addEventListener("click", () => {
        const willOpen = adminGallery.classList.contains("is-hidden");
        adminGallery.classList.toggle("is-hidden", !willOpen);
        toggleGalleryBtn.setAttribute("aria-expanded", String(willOpen));
        toggleGalleryBtn.querySelector("strong").textContent = willOpen ? "Close Gallery" : "Open Gallery";

        if (willOpen) {
            adminGallery.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    });
}

const closeModal = () => {
    if (!imageModal) return;
    imageModal.classList.remove("is-open");
    imageModal.setAttribute("aria-hidden", "true");
    if (modalImage) modalImage.src = "";
};

if (thumbnailButtons.length && imageModal && modalImage && closeImageModal) {
    thumbnailButtons.forEach((button) => {
        button.addEventListener("click", () => {
            modalImage.src = button.dataset.fullSrc;
            modalImage.alt = button.dataset.fullTitle || "Full image preview";
            if (modalImageTitle) {
                modalImageTitle.textContent = button.dataset.fullTitle || "";
            }
            imageModal.classList.add("is-open");
            imageModal.setAttribute("aria-hidden", "false");
        });
    });

    closeImageModal.addEventListener("click", closeModal);
    imageModal.addEventListener("click", (event) => {
        if (event.target === imageModal) closeModal();
    });
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") closeModal();
    });
}

const noticePdfInput = document.getElementById("noticePdfInput");
const noticeDropzone = document.getElementById("noticeDropzone");
const noticeFileName = document.getElementById("noticeFileName");

if (noticePdfInput && noticeDropzone && noticeFileName) {
    const updateNoticeFileName = (file) => {
        noticeFileName.textContent = file ? file.name : "No file selected";
    };

    noticePdfInput.addEventListener("change", function(event) {
        updateNoticeFileName(event.target.files[0]);
    });

    ["dragenter", "dragover"].forEach((eventName) => {
        noticeDropzone.addEventListener(eventName, (event) => {
            event.preventDefault();
            noticeDropzone.classList.add("is-dragging");
        });
    });

    ["dragleave", "drop"].forEach((eventName) => {
        noticeDropzone.addEventListener(eventName, (event) => {
            event.preventDefault();
            noticeDropzone.classList.remove("is-dragging");
        });
    });

    noticeDropzone.addEventListener("drop", (event) => {
        const file = event.dataTransfer.files[0];
        if (!file) return;

        if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
            updateNoticeFileName(null);
            noticeFileName.textContent = "Only PDF files are allowed";
            return;
        }

        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        noticePdfInput.files = dataTransfer.files;
        updateNoticeFileName(file);
    });
}
