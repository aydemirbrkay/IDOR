// Ortak yardımcılar: tüm sayfalar için
(function () {
  // 1) Mod rozetini doldur (her sayfada görünür)
  const modePill = document.getElementById("mode-pill");
  async function refreshModePill() {
    if (!modePill) return;
    try {
      const res = await fetch("/admin/mode");
      const data = await res.json();
      if (data.secure) {
        modePill.textContent = "MOD: SECURE";
        modePill.className = "pill pill-ok";
      } else {
        modePill.textContent = "MOD: VULNERABLE";
        modePill.className = "pill pill-bad";
      }
    } catch (e) { /* sessiz */ }
  }
  refreshModePill();
  setInterval(refreshModePill, 2000);

  // 2) Çıkış butonu
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      await fetch("/api/logout", { method: "POST" });
      window.location.href = "/login";
    });
  }
})();

// Fatura kartı (dashboard & saldırı laboratuvarı tarafından kullanılır)
function renderInvoiceCard(inv) {
  return `
    <div class="invoice-card">
      <div class="invoice-head">
        <span class="invoice-id">#${inv.id}</span>
        <span class="invoice-amount">${inv.amount}</span>
      </div>
      <div class="invoice-body">
        <div><span class="muted">Hizmet:</span> ${inv.service}</div>
        <div><span class="muted">Sahip:</span> ${inv.owner}</div>
        <div><span class="muted">Tarih:</span> ${inv.date}</div>
        <div><span class="muted">Durum:</span> ${inv.status}</div>
      </div>
    </div>
  `;
}
