const menuToggle = document.getElementById("menuToggle");
const sidebar = document.getElementById("sidebar");
const courseSearch = document.getElementById("courseSearch");
const courseRows = Array.from(document.querySelectorAll("#coursesTable tr")).slice(1);
const statCards = document.querySelectorAll(".stat-card");
const focusCourses = document.getElementById("focusCourses");
const coursesPanel = document.getElementById("coursesPanel");

if (menuToggle && sidebar) {
  menuToggle.addEventListener("click", () => {
    sidebar.classList.toggle("is-open");
  });
}

if (courseSearch) {
  courseSearch.addEventListener("input", (event) => {
    const query = event.target.value.trim().toLowerCase();

    courseRows.forEach((row) => {
      const text = row.innerText.toLowerCase();
      row.classList.toggle("is-hidden", !text.includes(query));
    });
  });
}

if (focusCourses && coursesPanel) {
  focusCourses.addEventListener("click", () => {
    coursesPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    courseSearch?.focus();
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
