document.getElementById("imageInput").addEventListener("change", function(event) {
    const file = event.target.files[0];
    const preview = document.getElementById("preview");

    if (file) {
        preview.src = URL.createObjectURL(file);
        preview.style.display = "block";
    }
});

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
