// Decorative animation only. Existing CampusOne authentication is not changed.
const group = document.getElementById('ribbon-lines');
const paths = Array.from({ length: 12 }, () => {
  const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  path.style.opacity = String(0.25 + 0.65 * Math.sin((group.childElementCount + 1) / 13 * Math.PI));
  group.append(path);
  return path;
});
let paused = false;
let frame = null;
let elapsed = 0;
let previousTime = null;
function draw(time) {
  paths.forEach((path, i) => {
    const spread = (i - 5.5) * 9;
    const wave = Math.sin(time + i * .09) * 28;
    const bend = Math.cos(time * .8 + i * .07) * 22;
    path.setAttribute('d', `M ${100 + spread} -40 C ${80 + spread + wave} 115, ${510 + spread} 130, ${330 + wave} 290 S ${200 + spread + bend} 465, ${365 + wave} 540 S ${450 + spread} 710, ${650 + spread} 850`);
  });
}
function animate(now) {
  if (previousTime !== null) elapsed += Math.min(now - previousTime, 50);
  previousTime = now;
  draw(elapsed / 10000 * Math.PI * 2);
  frame = requestAnimationFrame(animate);
}
function sync() {
  cancelAnimationFrame(frame);
  previousTime = null;
  if (!paused && !document.hidden) frame = requestAnimationFrame(animate);
}
document.addEventListener('visibilitychange', sync);
draw(0);
sync();

const landingThemeToggle = document.getElementById("landing-theme-toggle");

function applyLandingTheme() {
  const isLight =
    localStorage.getItem("campusone_theme") === "light";

  document.body.classList.toggle("landing-light-theme", isLight);

  if (landingThemeToggle) {
    landingThemeToggle.setAttribute(
      "aria-pressed",
      String(isLight)
    );

    landingThemeToggle.querySelector("span").textContent =
      isLight ? "Dark mode" : "Light mode";

    landingThemeToggle.firstChild.textContent =
      isLight ? "☾ " : "☼ ";
  }
}

landingThemeToggle?.addEventListener("click", () => {
  const isLight =
    document.body.classList.toggle("landing-light-theme");

  localStorage.setItem(
    "campusone_theme",
    isLight ? "light" : "dark"
  );

  applyLandingTheme();
});

applyLandingTheme();