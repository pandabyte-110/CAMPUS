const menuToggle = document.getElementById("menuToggle");
const sidebar = document.getElementById("sidebar");
const statCards = document.querySelectorAll(".stat-card");
const focusProfile = document.getElementById("focusProfile");
const profilePanel = document.getElementById("profilePanel");

if (menuToggle && sidebar) {
  menuToggle.addEventListener("click", () => {
    sidebar.classList.toggle("is-open");
  });
}

if (focusProfile && profilePanel) {
  focusProfile.addEventListener("click", () => {
    profilePanel.scrollIntoView({ behavior: "smooth", block: "start" });
  });
}

statCards.forEach((card, index) => {
  card.animate(
    [
      { opacity: 0, transform: "translateY(18px)" },
      { opacity: 1, transform: "translateY(0)" }
    ],
    {
      duration: 450,
      delay: index * 120,
      fill: "forwards",
      easing: "ease-out"
    }
  );
});
