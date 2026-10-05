(function () {
  var root = document.documentElement, tabs = [].slice.call(document.querySelectorAll(".tab")), views = [].slice.call(document.querySelectorAll(".view"));
  function show(i) {
    tabs.forEach(function (t, k) { t.setAttribute("aria-selected", k === i ? "true" : "false"); });
    views.forEach(function (v, k) { v.hidden = k !== i; });
    try { history.replaceState(null, "", "#" + views[i].id); } catch (e) {}
    window.scrollTo(0, 0);
  }
  tabs.forEach(function (t, i) { t.addEventListener("click", function () { show(i); }); });
  var h = (location.hash || "").slice(1), start = Math.max(0, views.findIndex(function (v) { return v.id === h; }));
  show(start);
  // thème
  var btn = document.getElementById("theme");
  function setTheme(t) { root.setAttribute("data-theme", t); btn.textContent = t === "dark" ? "Mode clair" : "Mode sombre"; try { localStorage.setItem("banklens-theme", t); } catch (e) {} }
  var saved = null; try { saved = localStorage.getItem("banklens-theme"); } catch (e) {}
  setTheme(saved || (window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
  btn.addEventListener("click", function () { setTheme(root.getAttribute("data-theme") === "dark" ? "light" : "dark"); });
  // info-bulle
  var tip = document.getElementById("tip");
  function move(e) { tip.style.left = Math.min(e.clientX + 14, window.innerWidth - tip.offsetWidth - 8) + "px"; tip.style.top = (e.clientY + 16) + "px"; }
  document.addEventListener("mouseover", function (e) { var t = e.target.closest("[data-tip]"); if (t) { tip.textContent = t.getAttribute("data-tip"); tip.hidden = false; move(e); } });
  document.addEventListener("mousemove", function (e) { if (!tip.hidden) move(e); });
  document.addEventListener("mouseout", function (e) { if (e.target.closest("[data-tip]")) tip.hidden = true; });
})();
