// QA: open index.html at desktop and phone widths, log console errors, take screenshots to qa/.
// Run from the study root with a static server (python3 -m http.server 8851; set PORT to change).
const { chromium } = require("playwright");
// Leaflet from a local npm copy (the CDN is not reachable from the build container); tiles and fonts are blocked here.
const LEAF = process.env.LEAFLET_DIST || "/dev/shm/lost/npm/node_modules/leaflet/dist";
(async () => {
  const b = await chromium.launch();
  const errs = [];
  for (const [nm, vw, vh] of (process.env.ONLY ? [[process.env.ONLY, process.env.ONLY === "phone" ? 390 : 1280, 900]] : [["desktop", 1280, 900], ["phone", 390, 844]])) {
    const p = await b.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: nm === "phone" ? 2 : 1 });
    await p.route(/arcgisonline|googleapis|gstatic/, r => r.abort());
    await p.route(/leaflet.min.js/, r => r.fulfill({ path: LEAF + "/leaflet.js" }));
    await p.route(/leaflet.min.css/, r => r.fulfill({ path: LEAF + "/leaflet.css" }));
    p.on("console", m => { if (m.type() === "error" && !/ERR_FAILED|net::/.test(m.text())) errs.push(nm + ": " + m.text()); });
    p.on("pageerror", e => errs.push(nm + " pageerror: " + e.message));
    await p.goto("http://localhost:" + (process.env.PORT || 8851) + "/index.html", { waitUntil: "networkidle" });
    await p.waitForTimeout(3000);
    await p.screenshot({ path: `qa/${nm}_top.png` });
    const shot = async (sel, f) => { await p.locator(sel).scrollIntoViewIfNeeded(); await p.waitForTimeout(700); await p.locator(sel).screenshot({ path: `qa/${nm}_${f}.png` }); };
    await shot("#atlas", "map");
    const t0 = Date.now(); await p.evaluate(() => trk.draw()); console.log(nm, "redraw all ms", Date.now() - t0);
    await p.click('#perRow [data-p="sat"]'); await p.waitForTimeout(800); await shot("#atlas", "sat");
    await p.click('#minRow [data-m="5"]'); await p.waitForTimeout(600); await shot("#atlas", "cat4");
    await p.click('#minRow [data-m="-1"]');
    await p.fill("#q", "Katrina 2005"); await p.waitForTimeout(800); await p.keyboard.press("Enter"); await p.waitForTimeout(2000); await shot("#atlas", "search_katrina");
    await p.fill("#q", "Haiyan"); await p.waitForTimeout(800); await p.keyboard.press("Enter"); await p.waitForTimeout(2000); await shot("#atlas", "search_haiyan");
    // a single season
    await p.evaluate(() => { const r = document.getElementById("yr"); r.value = 2005; r.dispatchEvent(new Event("input")); }); await p.waitForTimeout(1200);
    await p.evaluate(() => map.setView(...HOME())); await p.waitForTimeout(900); await shot("#atlas", "season2005");
    // click a track in the 2005 season
    await p.evaluate(() => { const s = T.list.find(x => x.nm === "Wilma" && x.season === 2005); const i = 20; const pt = map.latLngToContainerPoint([s.lat[i], s.lon[i]]); map.fire("click", { latlng: map.containerPointToLatLng(pt), containerPoint: pt }); });
    await p.waitForTimeout(900); await shot("#atlas", "click_wilma");
    await p.click('#perRow [data-p="all"]'); await p.waitForTimeout(500);
    await p.click(".lyrBtn"); await p.waitForTimeout(300);
    await p.evaluate(() => document.querySelector('.lyrPanel [data-k="lf"]').click()); await p.waitForTimeout(1500); await shot("#map", "layers_panel"); await p.click(".lyrBtn");
    await p.click("#lfTable tr[data-i='1']"); await p.waitForTimeout(1800); await shot("#atlas", "country_philippines");
    await p.click("#showGen"); await p.waitForTimeout(1500); await shot("#atlas", "genesis");
    await p.click('.lyrBtn'); await p.click('.lyrPanel .reset'); await p.click('.lyrBtn');
    await p.evaluate(() => map.setView(...HOME()));
    for (const c of ["pyChart", "monChart", "lfTable", "rgTable", "stTable", "shChart", "lmiChart", "lbChart"]) await shot("#" + c, c);
    await p.click('#pyRow [data-k="all"]'); await p.waitForTimeout(400); await shot("#pyChart", "pyChart_all");
    await p.click('#shRow .btn:nth-child(3)'); await p.waitForTimeout(400); await shot("#shChart", "shChart_NA");
    await p.click('#shRow .btn:nth-child(5)'); await p.waitForTimeout(400); await shot("#shChart", "shChart_WP");
    if (nm === "phone") {
      await p.click("#theme"); await p.waitForTimeout(1500); await shot("#atlas", "dark_map"); await shot("#shChart", "dark_shChart");
      await p.locator("#atlas").scrollIntoViewIfNeeded(); await p.click(".mfs-btn"); await p.waitForTimeout(1500); await p.screenshot({ path: `qa/${nm}_fullscreen.png` });
    }
    const ov = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    console.log(nm, "horizontal overflow px:", ov);
    await p.close();
  }
  console.log("errors:", errs.length ? errs : "none");
  await b.close();
})();
