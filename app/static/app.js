document.addEventListener("DOMContentLoaded", () => {
  const themeToggleBtn = document.getElementById("theme-toggle");
  const storedTheme = localStorage.getItem("nuvemlab-theme");
  const systemPrefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  
  const currentTheme = storedTheme || (systemPrefersDark ? "dark" : "light");
  document.documentElement.setAttribute("data-theme", currentTheme);

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", () => {
      const activeTheme = document.documentElement.getAttribute("data-theme");
      const nextTheme = activeTheme === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", nextTheme);
      localStorage.setItem("nuvemlab-theme", nextTheme);
      showToast(`Tema alterado para modo ${nextTheme === "dark" ? "Escuro" : "Claro"}.`, "info");
    });
  }

  const scrollProgressBar = document.getElementById("scroll-progress");
  const backToTopBtn = document.getElementById("back-to-top");

  window.addEventListener("scroll", () => {
    const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
    if (totalHeight > 0 && scrollProgressBar) {
      const progress = (window.scrollY / totalHeight) * 100;
      scrollProgressBar.style.width = `${progress}%`;
    }

    if (backToTopBtn) {
      if (window.scrollY > 320) {
        backToTopBtn.classList.add("is-visible");
      } else {
        backToTopBtn.classList.remove("is-visible");
      }
    }
  }, { passive: true });

  if (backToTopBtn) {
    backToTopBtn.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  const mobileMenuBtn = document.getElementById("mobile-menu-btn");
  const mobileDrawer = document.getElementById("mobile-drawer");
  const mobileDrawerOverlay = document.getElementById("mobile-drawer-overlay");
  const mobileDrawerClose = document.getElementById("mobile-drawer-close");
  const mobileNavLinks = document.querySelectorAll(".mobile-nav-list a");

  function openMobileDrawer() {
    mobileDrawer?.classList.add("is-active");
    mobileDrawerOverlay?.classList.add("is-active");
    mobileMenuBtn?.setAttribute("aria-expanded", "true");
    document.body.style.overflow = "hidden";
  }

  function closeMobileDrawer() {
    mobileDrawer?.classList.remove("is-active");
    mobileDrawerOverlay?.classList.remove("is-active");
    mobileMenuBtn?.setAttribute("aria-expanded", "false");
    document.body.style.overflow = "";
  }

  mobileMenuBtn?.addEventListener("click", openMobileDrawer);
  mobileDrawerClose?.addEventListener("click", closeMobileDrawer);
  mobileDrawerOverlay?.addEventListener("click", closeMobileDrawer);
  mobileNavLinks.forEach(link => link.addEventListener("click", closeMobileDrawer));

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && mobileDrawer?.classList.contains("is-active")) {
      closeMobileDrawer();
    }
  });

  const archNodes = {
    client: {
      category: "Camada de Entrada",
      title: "Cliente HTTPS & Consumidores da API",
      desc: "Navegadores modernos, pipelines externos e clientes cURL comunicam-se via chamadas REST com criptografia ponta a ponta TLS 1.3.",
      protocol: "HTTPS / HTTP/2 (TLS 1.3)",
      port: "443 / 80",
      security: "HSTS, CSP, COOP, CORS & Sanitização",
      latency: "< 15 ms",
      tech: ["Navegador Moderno", "cURL", "Fetch API", "PWA Ready"],
      status: "Online (Ativo)"
    },
    azure: {
      category: "PaaS Hosting & Ingress",
      title: "Azure App Service Linux & WAF",
      desc: "Termina conexões TLS, oferece mitigação de ataques DDoS L3/L4, balanceamento de carga inteligente e suporte a swap de slots sem downtime.",
      protocol: "TCP / Reverse Proxy TLS",
      port: "443 -> 8000",
      security: "Azure WAF L7, Zero Trust & OIDC Federated",
      latency: "~4 ms",
      tech: ["Azure App Service", "Linux Container", "Health Probes", "ACR"],
      status: "Online (PaaS Gerenciado)"
    },
    docker: {
      category: "Compute & Runtime ASGI",
      title: "Container Docker com FastAPI & Uvicorn",
      desc: "Executa a aplicação Python 3.13-slim sob usuário não-root (UID 10001), sistema de arquivos em modo somente leitura (read-only) e rate limiting por IP.",
      protocol: "ASGI / HTTP 1.1",
      port: "8000 (Interna)",
      security: "UID 10001 (Não-Root), Read-Only FS, Rate Limiter",
      latency: "~2.5 ms",
      tech: ["Python 3.13-slim", "FastAPI 0.115", "Uvicorn ASGI", "Pydantic v2"],
      status: "Online (UID 10001)"
    },
    sqlite: {
      category: "Armazenamento & Persistência",
      title: "Volume Persistente SQLite WAL",
      desc: "Engine relacional operando com Write-Ahead Logging (WAL), permitindo leituras concorrentes sem bloqueio de escrita e mantendo os dados entre recriações do container.",
      protocol: "POSIX File I/O (WAL)",
      port: "Local VFS (/home/data)",
      security: "Named Volume, WAL Concurrency, ACID Integrity",
      latency: "< 1.0 ms",
      tech: ["SQLite 3", "WAL Mode", "Docker Named Volume", "Busy Timeout 5s"],
      status: "Persistido (WAL Ativo)"
    }
  };

  const archNodeButtons = document.querySelectorAll(".arch-node-btn");
  const archDetailCategory = document.getElementById("arch-detail-category");
  const archDetailTitle = document.getElementById("arch-detail-title");
  const archDetailDesc = document.getElementById("arch-detail-desc");
  const archDetailProtocol = document.getElementById("arch-detail-protocol");
  const archDetailPort = document.getElementById("arch-detail-port");
  const archDetailSecurity = document.getElementById("arch-detail-security");
  const archDetailLatency = document.getElementById("arch-detail-latency");
  const archDetailTech = document.getElementById("arch-detail-tech");
  const archDetailStatus = document.getElementById("arch-detail-status");

  archNodeButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      archNodeButtons.forEach(b => {
        b.classList.remove("is-active");
        b.setAttribute("aria-selected", "false");
      });
      btn.classList.add("is-active");
      btn.setAttribute("aria-selected", "true");

      const nodeKey = btn.dataset.archNode;
      const data = archNodes[nodeKey];
      if (data) {
        if (archDetailCategory) archDetailCategory.textContent = data.category;
        if (archDetailTitle) archDetailTitle.textContent = data.title;
        if (archDetailDesc) archDetailDesc.textContent = data.desc;
        if (archDetailProtocol) archDetailProtocol.textContent = data.protocol;
        if (archDetailPort) archDetailPort.textContent = data.port;
        if (archDetailSecurity) archDetailSecurity.textContent = data.security;
        if (archDetailLatency) archDetailLatency.textContent = data.latency;
        if (archDetailStatus) archDetailStatus.textContent = data.status;

        if (archDetailTech) {
          archDetailTech.innerHTML = data.tech.map(t => `<span>${t}</span>`).join("");
        }
      }
    });
  });

  const apiTabs = document.querySelectorAll(".api-tab");
  const apiMethodLabel = document.getElementById("api-current-method");
  const apiUrlInput = document.getElementById("api-current-url");
  const apiSendBtn = document.getElementById("api-send-btn");
  const apiBodyEditor = document.getElementById("api-body-editor");
  const apiPayloadInput = document.getElementById("api-payload-input");
  const apiResStatus = document.getElementById("api-res-status");
  const apiResLatency = document.getElementById("api-res-latency");
  const apiJsonOutput = document.getElementById("api-json-output");
  const apiCopyJsonBtn = document.getElementById("api-copy-json");

  let activeMethod = "GET";
  let activeUrl = "/api/servicos";

  apiTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      apiTabs.forEach(t => t.classList.remove("is-active"));
      tab.classList.add("is-active");

      activeMethod = tab.dataset.method || "GET";
      activeUrl = tab.dataset.url || "/api/servicos";

      if (apiMethodLabel) apiMethodLabel.textContent = activeMethod;
      if (apiUrlInput) apiUrlInput.value = activeUrl;

      if (activeMethod === "POST") {
        if (apiBodyEditor) apiBodyEditor.style.display = "block";
      } else {
        if (apiBodyEditor) apiBodyEditor.style.display = "none";
      }
    });
  });

  if (apiSendBtn) {
    apiSendBtn.addEventListener("click", async () => {
      apiSendBtn.classList.add("is-loading");
      apiSendBtn.disabled = true;

      const startTime = performance.now();

      try {
        const options = {
          method: activeMethod,
          headers: { "Content-Type": "application/json" }
        };

        if (activeMethod === "POST" && apiPayloadInput) {
          options.body = apiPayloadInput.value;
        }

        const response = await fetch(activeUrl, options);
        const endTime = performance.now();
        const duration = Math.round(endTime - startTime);

        if (apiResLatency) apiResLatency.textContent = `${duration} ms`;

        if (apiResStatus) {
          apiResStatus.textContent = `${response.status} ${response.statusText || ""}`.trim();
          apiResStatus.className = response.ok ? "status-chip chip-success" : "status-chip chip-error";
        }

        const responseData = await response.json();
        if (apiJsonOutput) {
          apiJsonOutput.innerHTML = `<code>${escapeHtml(JSON.stringify(responseData, null, 2))}</code>`;
        }

        if (activeUrl === "/api/contato" && response.ok) {
          fetchTelemetryMetrics();
        }
      } catch (err) {
        const endTime = performance.now();
        if (apiResLatency) apiResLatency.textContent = `${Math.round(endTime - startTime)} ms`;
        if (apiResStatus) {
          apiResStatus.textContent = "Erro de Rede / Timeout";
          apiResStatus.className = "status-chip chip-error";
        }
        if (apiJsonOutput) {
          apiJsonOutput.innerHTML = `<code>// Falha ao conectar: ${escapeHtml(err.message)}</code>`;
        }
      } finally {
        apiSendBtn.classList.remove("is-loading");
        apiSendBtn.disabled = false;
      }
    });
  }

  if (apiCopyJsonBtn && apiJsonOutput) {
    apiCopyJsonBtn.addEventListener("click", () => {
      const textToCopy = apiJsonOutput.textContent;
      navigator.clipboard.writeText(textToCopy).then(() => {
        showToast("JSON copiado para a área de transferência!", "success");
      });
    });
  }

  const sliderReqs = document.getElementById("slider-reqs");
  const sliderMem = document.getElementById("slider-mem");
  const sliderInst = document.getElementById("slider-inst");

  const valReqs = document.getElementById("val-reqs");
  const valMem = document.getElementById("val-mem");
  const valInst = document.getElementById("val-inst");

  const finopsSavings = document.getElementById("finops-savings-percent");
  const finopsCostAzure = document.getElementById("finops-cost-azure");
  const finopsCostOnprem = document.getElementById("finops-cost-onprem");
  const finopsThroughput = document.getElementById("finops-throughput");
  const finopsLatency = document.getElementById("finops-latency");

  function updateFinOpsCalculations() {
    if (!sliderReqs || !sliderMem || !sliderInst) return;

    const reqs = parseInt(sliderReqs.value, 10);
    const mem = parseInt(sliderMem.value, 10);
    const inst = parseInt(sliderInst.value, 10);

    if (valReqs) valReqs.textContent = reqs.toLocaleString("pt-BR");
    if (valMem) valMem.textContent = `${mem} MB`;
    if (valInst) valInst.textContent = `${inst} nó${inst > 1 ? "s" : ""}`;

    const costAzure = (13.0 * inst) + ((reqs / 1000000) * 0.40);
    const costOnprem = (45.0 * inst) + 25.0;
    const savings = Math.max(0, Math.round(((costOnprem - costAzure) / costOnprem) * 100));
    const rps = Math.max(50, Math.round((mem / 256) * 120 * inst));
    const latency = Math.max(8.0, 38.0 - (inst * 3.5)).toFixed(1);

    if (finopsSavings) finopsSavings.textContent = `${savings}% de redução`;
    if (finopsCostAzure) finopsCostAzure.textContent = `$${costAzure.toFixed(2)} / mês`;
    if (finopsCostOnprem) finopsCostOnprem.textContent = `$${costOnprem.toFixed(2)} / mês`;
    if (finopsThroughput) finopsThroughput.textContent = `${rps} req / seg`;
    if (finopsLatency) finopsLatency.textContent = `~${latency} ms`;
  }

  sliderReqs?.addEventListener("input", updateFinOpsCalculations);
  sliderMem?.addEventListener("input", updateFinOpsCalculations);
  sliderInst?.addEventListener("input", updateFinOpsCalculations);
  updateFinOpsCalculations();

  const telemetryStatus = document.getElementById("telemetry-status");
  const telemetryUptime = document.getElementById("telemetry-uptime");
  const telemetryContacts = document.getElementById("telemetry-contacts");
  const telemetryDb = document.getElementById("telemetry-db");
  const telemetryRefreshBtn = document.getElementById("telemetry-refresh-btn");
  const heroLatencyVal = document.getElementById("hero-latency-val");

  async function fetchTelemetryMetrics() {
    const startTime = performance.now();
    try {
      const res = await fetch("/api/status/metrics");
      const endTime = performance.now();
      const latency = Math.round(endTime - startTime);

      if (res.ok) {
        const data = await res.json();
        if (telemetryStatus) telemetryStatus.textContent = "Online (Operacional)";
        if (telemetryContacts) telemetryContacts.textContent = data.total_contatos;
        if (telemetryDb) telemetryDb.textContent = "WAL Concorrente";

        const seconds = Math.floor(data.uptime_segundos);
        const mins = Math.floor(seconds / 60);
        const hours = Math.floor(mins / 60);
        let uptimeStr = `${seconds}s`;
        if (hours > 0) uptimeStr = `${hours}h ${mins % 60}m`;
        else if (mins > 0) uptimeStr = `${mins}m ${seconds % 60}s`;

        if (telemetryUptime) telemetryUptime.textContent = uptimeStr;
        if (heroLatencyVal) heroLatencyVal.textContent = `~${latency} ms`;
      }
    } catch {
      if (telemetryStatus) telemetryStatus.textContent = "Degradado";
    }
  }

  telemetryRefreshBtn?.addEventListener("click", () => {
    fetchTelemetryMetrics();
    showToast("Métricas de telemetria atualizadas com sucesso.", "info");
  });

  fetchTelemetryMetrics();
  setInterval(fetchTelemetryMetrics, 30000);

  const contactForm = document.getElementById("contact-form");
  const formStatus = document.getElementById("form-status");
  const msgInput = document.getElementById("mensagem");
  const charCount = document.getElementById("char-count");
  const charProgress = document.getElementById("char-progress");
  const topicChips = document.querySelectorAll(".topic-chips .chip");
  const topicInput = document.getElementById("topico");

  topicChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      topicChips.forEach(c => c.classList.remove("is-active"));
      chip.classList.add("is-active");
      const chosenTopic = chip.dataset.topic;
      if (topicInput) topicInput.value = chosenTopic;
    });
  });

  if (msgInput && charCount && charProgress) {
    msgInput.addEventListener("input", () => {
      const len = msgInput.value.length;
      charCount.textContent = `${len} / 1.000`;
      const pct = Math.min(100, (len / 1000) * 100);
      charProgress.style.width = `${pct}%`;

      if (len > 900) {
        charProgress.style.backgroundColor = "var(--danger)";
      } else if (len > 700) {
        charProgress.style.backgroundColor = "var(--amber)";
      } else {
        charProgress.style.backgroundColor = "var(--azure)";
      }
    });
  }

  if (contactForm) {
    contactForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const submitBtn = contactForm.querySelector('button[type="submit"]');
      const formData = new FormData(contactForm);
      const payload = Object.fromEntries(formData.entries());

      if (payload.hp_website && payload.hp_website.trim() !== "") {
        showToast("Mensagem enviada com sucesso!", "success");
        contactForm.reset();
        return;
      }

      if (submitBtn) {
        submitBtn.classList.add("is-loading");
        submitBtn.disabled = true;
      }
      if (formStatus) {
        formStatus.textContent = "Validando dados e gravando no volume...";
        formStatus.dataset.state = "loading";
      }

      try {
        const response = await fetch("/api/contato", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (response.status === 429) {
          throw new Error("Limite de envios excedido (Rate Limit). Aguarde 1 minuto.");
        }

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || "Verifique os campos preenchidos e tente novamente.");
        }

        const result = await response.json();
        contactForm.reset();
        if (charCount) charCount.textContent = "0 / 1.000";
        if (charProgress) charProgress.style.width = "0%";

        const successMsg = `Mensagem gravada com sucesso! Protocolo #${result.protocolo || result.id}.`;
        if (formStatus) {
          formStatus.textContent = successMsg;
          formStatus.dataset.state = "success";
        }
        showToast(successMsg, "success");
        fetchTelemetryMetrics();
      } catch (err) {
        const errorMsg = err.message || "Falha na comunicação. Tente novamente.";
        if (formStatus) {
          formStatus.textContent = errorMsg;
          formStatus.dataset.state = "error";
        }
        showToast(errorMsg, "error");
      } finally {
        if (submitBtn) {
          submitBtn.classList.remove("is-loading");
          submitBtn.disabled = false;
        }
      }
    });
  }

  const copyButtons = document.querySelectorAll(".copy-btn[data-copy]");
  copyButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const textToCopy = btn.dataset.copy;
      if (textToCopy) {
        navigator.clipboard.writeText(textToCopy).then(() => {
          btn.classList.add("is-copied");
          const spanText = btn.querySelector("span");
          if (spanText) spanText.textContent = "Copiado!";
          showToast("Comando copiado para a área de transferência!", "info");

          setTimeout(() => {
            btn.classList.remove("is-copied");
            if (spanText) spanText.textContent = "Copiar";
          }, 2400);
        });
      }
    });
  });

  function showToast(message, type = "info") {
    const toastContainer = document.getElementById("toast-container");
    if (!toastContainer) return;

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<div>${escapeHtml(message)}</div>`;

    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(10px)";
      toast.style.transition = "opacity 300ms ease, transform 300ms ease";
      setTimeout(() => toast.remove(), 350);
    }, 4000);
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  const windowGroups = document.querySelectorAll("[data-window-group]");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  if (windowGroups.length && !reduceMotion.matches && "IntersectionObserver" in window) {
    document.documentElement.classList.add("motion-enabled");

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });

    windowGroups.forEach((group) => {
      group.querySelectorAll("[data-window]").forEach((el, index) => {
        el.style.setProperty("--window-delay", `${Math.min(index * 90, 300)}ms`);
      });
      observer.observe(group);
    });
  } else {
    windowGroups.forEach((group) => group.classList.add("is-visible"));
  }
});


