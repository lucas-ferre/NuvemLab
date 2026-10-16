document.addEventListener("DOMContentLoaded", () => {
  const themeToggleBtn = document.getElementById("theme-toggle");
  const themeLabel = document.getElementById("theme-label");
  const metaThemeColor = document.getElementById("meta-theme-color");
  const storedTheme = localStorage.getItem("nuvemlab-theme");
  const systemPrefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;

  const THEME_ORDER = ["dark", "azure", "light"];
  const THEME_NAMES = {
    dark: "Escuro (Dark)",
    azure: "Azure Deep",
    light: "Claro (Light)",
  };
  const THEME_BADGES = {
    dark: "Dark",
    azure: "Azure",
    light: "Light",
  };
  const THEME_COLORS = {
    dark: "#050d18",
    azure: "#04142c",
    light: "#f8fafc",
  };

  let themeSwitchTimer = null;

  function applyTheme(theme, notify = false) {
    const validTheme = THEME_ORDER.includes(theme) ? theme : "dark";
    const previousTheme = document.documentElement.getAttribute("data-theme") || "dark";

    if (notify && previousTheme !== validTheme && themeToggleBtn) {
      const outgoingIcon = themeToggleBtn.querySelector(`.theme-icon-${previousTheme}`);
      const incomingIcon = themeToggleBtn.querySelector(`.theme-icon-${validTheme}`);
      if (incomingIcon) incomingIcon.classList.remove("is-exiting");
      if (outgoingIcon) outgoingIcon.classList.add("is-exiting");
      themeToggleBtn.classList.remove("is-switching");
      void themeToggleBtn.offsetWidth;
      themeToggleBtn.classList.add("is-switching");
      if (themeSwitchTimer) clearTimeout(themeSwitchTimer);
      themeSwitchTimer = setTimeout(() => {
        if (outgoingIcon) outgoingIcon.classList.remove("is-exiting");
        themeToggleBtn.classList.remove("is-switching");
      }, 380);
    }

    document.documentElement.setAttribute("data-theme", validTheme);
    localStorage.setItem("nuvemlab-theme", validTheme);
    if (themeLabel) themeLabel.textContent = THEME_BADGES[validTheme];
    if (metaThemeColor) metaThemeColor.setAttribute("content", THEME_COLORS[validTheme]);
    if (notify) {
      showToast(`Tema alterado para modo ${THEME_NAMES[validTheme]}.`, "info");
    }
  }

  const initialTheme = storedTheme || (systemPrefersDark ? "dark" : "light");
  applyTheme(initialTheme, false);

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", () => {
      const activeTheme = document.documentElement.getAttribute("data-theme") || "dark";
      const nextIndex = (THEME_ORDER.indexOf(activeTheme) + 1) % THEME_ORDER.length;
      applyTheme(THEME_ORDER[nextIndex], true);
    });
  }

  const domainBadge = document.querySelector(".domain-name");
  if (domainBadge && window.location.host) {
    domainBadge.textContent =
      window.location.host.includes("localhost") || window.location.host.includes("127.0.0.1")
        ? "localhost:8000 (Modo Local)"
        : window.location.host;
  }

  const scrollProgressBar = document.getElementById("scroll-progress");
  const backToTopBtn = document.getElementById("back-to-top");

  window.addEventListener(
    "scroll",
    () => {
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
    },
    { passive: true }
  );

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
  mobileNavLinks.forEach((link) => link.addEventListener("click", closeMobileDrawer));

  const cmdTriggerBtn = document.getElementById("cmd-palette-trigger");
  const cmdBackdrop = document.getElementById("cmd-palette-backdrop");
  const cmdInput = document.getElementById("cmd-palette-input");
  const cmdEscBtn = document.getElementById("cmd-palette-esc");
  const cmdItems = document.querySelectorAll(".cmd-item");

  function openCommandPalette() {
    if (!cmdBackdrop) return;
    cmdBackdrop.classList.add("is-open");
    cmdBackdrop.setAttribute("aria-hidden", "false");
    if (cmdInput) {
      cmdInput.value = "";
      filterCommandItems("");
      setTimeout(() => cmdInput.focus(), 40);
    }
  }

  function closeCommandPalette() {
    if (!cmdBackdrop) return;
    cmdBackdrop.classList.remove("is-open");
    cmdBackdrop.setAttribute("aria-hidden", "true");
  }

  function filterCommandItems(query) {
    const q = query.trim().toLowerCase();
    cmdItems.forEach((item) => {
      const text = item.textContent?.toLowerCase() || "";
      item.style.display = !q || text.includes(q) ? "flex" : "none";
    });
  }

  cmdTriggerBtn?.addEventListener("click", openCommandPalette);
  cmdEscBtn?.addEventListener("click", closeCommandPalette);
  cmdBackdrop?.addEventListener("click", (e) => {
    if (e.target === cmdBackdrop) closeCommandPalette();
  });

  cmdInput?.addEventListener("input", () => {
    filterCommandItems(cmdInput.value);
  });

  cmdInput?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      const firstVisible = Array.from(cmdItems).find((el) => el.style.display !== "none");
      if (firstVisible) firstVisible.click();
    }
  });

  cmdItems.forEach((item) => {
    item.addEventListener("click", async () => {
      const action = item.dataset.cmdAction;
      closeCommandPalette();

      if (action === "goto") {
        const target = document.querySelector(item.dataset.target || "");
        target?.scrollIntoView({ behavior: "smooth" });
      } else if (action === "theme") {
        applyTheme(item.dataset.themeVal || "dark", true);
      } else if (action === "ping-health") {
        const t0 = performance.now();
        try {
          const r = await fetch("/health");
          const ms = Math.round(performance.now() - t0);
          if (r.ok) {
            showToast(`Healthcheck /health OK (200) em ${ms} ms! SQLite WAL operacional.`, "success");
          }
        } catch {
          showToast("Falha ao consultar /health.", "error");
        }
      } else if (action === "copy-docker") {
        navigator.clipboard?.writeText("docker compose up --build");
        showToast("Comando 'docker compose up --build' copiado!", "info");
      } else if (action === "open-swagger") {
        window.open("/docs", "_blank", "noopener");
      }
    });
  });

  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      if (cmdBackdrop?.classList.contains("is-open")) {
        closeCommandPalette();
      } else {
        openCommandPalette();
      }
    } else if (e.key === "Escape") {
      if (cmdBackdrop?.classList.contains("is-open")) {
        closeCommandPalette();
      }
      if (mobileDrawer?.classList.contains("is-active")) {
        closeMobileDrawer();
      }
    }
  });

  const archNodes = {
    client: {
      category: "Camada de Entrada",
      title: "Cliente HTTPS & Consumidores da API",
      desc: "Navegadores modernos, pipelines externos e clientes cURL comunicam-se via chamadas REST com criptografia ponta a ponta TLS 1.3.",
      protocol: "HTTPS / HTTP/2 (TLS 1.3)",
      port: "443 / 80",
      security: "HSTS, CSP, COOP, CORP & Sanitização",
      latency: "< 15 ms",
      tech: ["Navegador Moderno", "cURL", "Fetch API", "Command Palette"],
      status: "Online (Ativo)",
      endpoint: "servicos",
      pingUrl: "/api/servicos",
    },
    azure: {
      category: "PaaS Hosting & Ingress",
      title: "Azure App Service Linux & WAF",
      desc: "Termina conexões TLS, oferece mitigação de ataques DDoS L3/L4, balanceamento de carga inteligente e suporte a swap de slots sem downtime.",
      protocol: "TCP / Reverse Proxy TLS",
      port: "443 -> 8000",
      security: "Azure WAF L7, Zero Trust & OIDC Federated",
      latency: "~4 ms",
      tech: ["Azure App Service", "Linux Container", "Slot Staging Swap", "ACR"],
      status: "Online (PaaS Gerenciado)",
      endpoint: "health",
      pingUrl: "/health",
    },
    docker: {
      category: "Compute & Runtime ASGI",
      title: "Container Docker com FastAPI & Uvicorn",
      desc: "Executa a aplicação Python 3.13-slim sob usuário não-root (UID 10001), sistema de arquivos em modo somente leitura (read-only) e rate limiting por IP.",
      protocol: "ASGI / HTTP 1.1 (GZip)",
      port: "8000 (Interna)",
      security: "UID 10001 (Não-Root), Read-Only FS, Rate Limiter",
      latency: "~2.5 ms",
      tech: ["Python 3.13-slim", "FastAPI 0.115", "Uvicorn ASGI", "Pydantic v2"],
      status: "Online (UID 10001)",
      endpoint: "metrics",
      pingUrl: "/api/status/metrics",
    },
    sqlite: {
      category: "Armazenamento & Persistência",
      title: "Volume Persistente SQLite WAL",
      desc: "Engine relacional operando com Write-Ahead Logging (WAL), permitindo leituras concorrentes sem bloqueio de escrita e mantendo os dados entre recriações do container.",
      protocol: "POSIX File I/O (WAL)",
      port: "Local VFS (/home/data)",
      security: "Named Volume, WAL Concurrency, LGPD Masking",
      latency: "< 1.0 ms",
      tech: ["SQLite 3", "WAL Mode", "Docker Named Volume", "Busy Timeout 5s"],
      status: "Persistido (WAL Ativo)",
      endpoint: "recentes",
      pingUrl: "/api/contatos/recentes",
    },
  };

  let currentArchKey = "client";
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
  const archPingBtn = document.getElementById("arch-ping-btn");
  const archTestApiBtn = document.getElementById("arch-test-api-btn");

  function selectArchNode(nodeKey) {
    const data = archNodes[nodeKey];
    if (!data) return;
    currentArchKey = nodeKey;

    archNodeButtons.forEach((b) => {
      const isMatch = b.dataset.archNode === nodeKey;
      b.classList.toggle("is-active", isMatch);
      b.setAttribute("aria-selected", isMatch ? "true" : "false");
    });

    if (archDetailCategory) archDetailCategory.textContent = data.category;
    if (archDetailTitle) archDetailTitle.textContent = data.title;
    if (archDetailDesc) archDetailDesc.textContent = data.desc;
    if (archDetailProtocol) archDetailProtocol.textContent = data.protocol;
    if (archDetailPort) archDetailPort.textContent = data.port;
    if (archDetailSecurity) archDetailSecurity.textContent = data.security;
    if (archDetailLatency) archDetailLatency.textContent = data.latency;
    if (archDetailStatus) archDetailStatus.textContent = data.status;
    if (archTestApiBtn) archTestApiBtn.dataset.targetEndpoint = data.endpoint;

    if (archDetailTech) {
      archDetailTech.innerHTML = data.tech.map((t) => `<span>${escapeHtml(t)}</span>`).join("");
    }
  }

  archNodeButtons.forEach((btn, idx) => {
    btn.addEventListener("click", () => {
      selectArchNode(btn.dataset.archNode || "client");
    });

    btn.addEventListener("keydown", (e) => {
      if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
        e.preventDefault();
        const dir = e.key === "ArrowRight" ? 1 : -1;
        const nextIdx = (idx + dir + archNodeButtons.length) % archNodeButtons.length;
        const nextBtn = archNodeButtons[nextIdx];
        nextBtn.focus();
        selectArchNode(nextBtn.dataset.archNode || "client");
      }
    });
  });

  document.querySelectorAll(".flow-node[data-hero-arch]").forEach((node) => {
    const triggerHeroNode = () => {
      const targetKey = node.dataset.heroArch || "client";
      selectArchNode(targetKey);
      document.getElementById("arquitetura")?.scrollIntoView({ behavior: "smooth" });
    };
    node.addEventListener("click", triggerHeroNode);
    node.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        triggerHeroNode();
      }
    });
  });

  archPingBtn?.addEventListener("click", async () => {
    const data = archNodes[currentArchKey];
    if (!data) return;
    const t0 = performance.now();
    try {
      const res = await fetch(data.pingUrl);
      const rtt = Math.round(performance.now() - t0);
      const serverTime = res.headers.get("x-process-time-ms") || `${rtt}`;
      if (archDetailLatency) {
        archDetailLatency.textContent = `${rtt} ms (ASGI: ${serverTime} ms)`;
      }
      showToast(`Camada "${data.title}" respondeu em ${rtt} ms (Processamento: ${serverTime} ms).`, "success");
    } catch {
      showToast("Não foi possível medir a latência da camada.", "error");
    }
  });

  archTestApiBtn?.addEventListener("click", () => {
    const targetEndpoint = archTestApiBtn.dataset.targetEndpoint || "servicos";
    const matchingTab = document.querySelector(`.api-tab[data-endpoint="${targetEndpoint}"]`);
    if (matchingTab) {
      matchingTab.click();
      document.getElementById("api-playground")?.scrollIntoView({ behavior: "smooth" });
      setTimeout(() => document.getElementById("api-send-btn")?.click(), 350);
    }
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
  const apiViewBtns = document.querySelectorAll(".api-view-btn");

  const DEFAULT_PAYLOADS = {
    contato: JSON.stringify(
      {
        nome: "Desenvolvedor Teste",
        email: "dev@exemplo.com",
        topico: "Arquitetura Cloud",
        mensagem: "Testando o console interativo da API NuvemLab.",
      },
      null,
      2
    ),
    simulador: JSON.stringify(
      {
        requisicoes_mes: 250000,
        memoria_mb: 1024,
        instancias: 2,
        perfil: "standard",
      },
      null,
      2
    ),
  };

  let activeEndpointKey = "servicos";
  let activeMethod = "GET";
  let activeUrl = "/api/servicos";
  let activeResponseView = "json";
  let lastJsonResponse = "// Clique em \"Executar Requisição\" para ver a resposta em tempo real...";
  let lastHeadersResponse = {};

  function buildCurlCommand() {
    const origin = window.location.origin || "http://localhost:8000";
    if (activeMethod === "POST" && apiPayloadInput) {
      const compactBody = apiPayloadInput.value.replace(/\s+/g, " ").trim();
      return `curl -i -X POST "${origin}${activeUrl}" \\\n  -H "Content-Type: application/json" \\\n  -d '${compactBody}'`;
    }
    return `curl -i -X GET "${origin}${activeUrl}"`;
  }

  function renderConsoleOutput() {
    if (!apiJsonOutput) return;

    if (activeResponseView === "json") {
      if (typeof lastJsonResponse === "string" && lastJsonResponse.startsWith("//")) {
        apiJsonOutput.innerHTML = `<code><span class="json-null">${escapeHtml(lastJsonResponse)}</span></code>`;
      } else {
        apiJsonOutput.innerHTML = `<code>${syntaxHighlight(lastJsonResponse)}</code>`;
      }
    } else if (activeResponseView === "headers") {
      const keys = Object.keys(lastHeadersResponse);
      if (!keys.length) {
        apiJsonOutput.innerHTML = `<code><span class="json-null">// Execute uma requisição para inspecionar os cabeçalhos HTTP e OWASP...</span></code>`;
      } else {
        const lines = keys.map((k) => {
          const val = escapeHtml(lastHeadersResponse[k]);
          return `<span class="json-key">"${escapeHtml(k)}"</span>: <span class="json-string">"${val}"</span>`;
        });
        apiJsonOutput.innerHTML = `<code>{\n  ${lines.join(",\n  ")}\n}</code>`;
      }
    } else if (activeResponseView === "curl") {
      apiJsonOutput.innerHTML = `<code>${escapeHtml(buildCurlCommand())}</code>`;
    }
  }

  apiViewBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      apiViewBtns.forEach((b) => b.classList.remove("is-active"));
      btn.classList.add("is-active");
      activeResponseView = btn.dataset.view || "json";
      const copySpan = apiCopyJsonBtn?.querySelector("span");
      if (copySpan) {
        copySpan.textContent =
          activeResponseView === "curl"
            ? "Copiar cURL"
            : activeResponseView === "headers"
              ? "Copiar Headers"
              : "Copiar JSON";
      }
      renderConsoleOutput();
    });
  });

  apiTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      apiTabs.forEach((t) => t.classList.remove("is-active"));
      tab.classList.add("is-active");

      activeEndpointKey = tab.dataset.endpoint || "servicos";
      activeMethod = tab.dataset.method || "GET";
      activeUrl = tab.dataset.url || "/api/servicos";

      if (apiMethodLabel) {
        apiMethodLabel.textContent = activeMethod;
        apiMethodLabel.style.color = activeMethod === "POST" ? "var(--azure)" : "var(--emerald)";
      }
      if (apiUrlInput) apiUrlInput.value = activeUrl;

      if (activeMethod === "POST") {
        if (apiBodyEditor) apiBodyEditor.style.display = "block";
        if (apiPayloadInput && DEFAULT_PAYLOADS[activeEndpointKey]) {
          apiPayloadInput.value = DEFAULT_PAYLOADS[activeEndpointKey];
        }
      } else {
        if (apiBodyEditor) apiBodyEditor.style.display = "none";
      }

      if (activeResponseView === "curl") {
        renderConsoleOutput();
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
          headers: { "Content-Type": "application/json" },
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

        const headersObj = {};
        response.headers.forEach((val, key) => {
          headersObj[key] = val;
        });
        lastHeadersResponse = headersObj;

        lastJsonResponse = await response.json();
        renderConsoleOutput();

        if (activeUrl === "/api/contato" && response.ok) {
          fetchTelemetryMetrics();
          fetchRecentContacts();
        }
      } catch (err) {
        const endTime = performance.now();
        if (apiResLatency) apiResLatency.textContent = `${Math.round(endTime - startTime)} ms`;
        if (apiResStatus) {
          apiResStatus.textContent = "Erro de Rede / JSON";
          apiResStatus.className = "status-chip chip-error";
        }
        lastJsonResponse = `// Falha ao processar requisição: ${err.message}`;
        renderConsoleOutput();
      } finally {
        apiSendBtn.classList.remove("is-loading");
        apiSendBtn.disabled = false;
      }
    });
  }

  if (apiCopyJsonBtn && apiJsonOutput) {
    apiCopyJsonBtn.addEventListener("click", () => {
      const textToCopy = apiJsonOutput.textContent || "";
      navigator.clipboard.writeText(textToCopy).then(() => {
        showToast("Conteúdo copiado para a área de transferência!", "success");
      });
    });
  }

  const sliderReqs = document.getElementById("slider-reqs");
  const sliderMem = document.getElementById("slider-mem");
  const sliderInst = document.getElementById("slider-inst");
  const profileTabs = document.querySelectorAll(".profile-tab");

  const valReqs = document.getElementById("val-reqs");
  const valMem = document.getElementById("val-mem");
  const valInst = document.getElementById("val-inst");

  const finopsSavings = document.getElementById("finops-savings-percent");
  const finopsAnnualSavings = document.getElementById("finops-annual-savings");
  const finopsCostAzure = document.getElementById("finops-cost-azure");
  const finopsCostOnprem = document.getElementById("finops-cost-onprem");
  const finopsThroughput = document.getElementById("finops-throughput");
  const finopsLatency = document.getElementById("finops-latency");
  const finopsTierRec = document.getElementById("finops-tier-rec");
  const finopsExportBtn = document.getElementById("finops-export-btn");

  let activeFinopsProfile = "standard";
  let lastFinopsResult = {};
  let finopsDebounceTimer = null;

  function applyFinOpsVisuals(data) {
    lastFinopsResult = data;

    if (finopsSavings) finopsSavings.textContent = `${Math.round(data.economia_percentual)}% de redução`;
    if (finopsAnnualSavings) {
      finopsAnnualSavings.textContent = `Economia anual: ~$${data.economia_anual_usd.toFixed(2)}/ano • SLA ${data.sla_disponibilidade}`;
    }
    if (finopsCostAzure) finopsCostAzure.textContent = `$${data.custo_azure_app_service.toFixed(2)} / mês`;
    if (finopsCostOnprem) finopsCostOnprem.textContent = `$${data.custo_on_premise_estimado.toFixed(2)} / mês`;
    if (finopsThroughput) finopsThroughput.textContent = `${data.requisicoes_suportadas_segundo} req / seg`;
    if (finopsLatency) finopsLatency.textContent = `~${data.latencia_media_ms.toFixed(1)} ms`;
    if (finopsTierRec) finopsTierRec.textContent = `${data.tier_recomendado} (${data.vcpu_alocada} vCPU)`;

    const barValAzure = document.getElementById("finops-bar-val-azure");
    const barValAca = document.getElementById("finops-bar-val-aca");
    const barValOnprem = document.getElementById("finops-bar-val-onprem");
    const chartFillAzure = document.getElementById("finops-chart-fill-azure");
    const chartFillAca = document.getElementById("finops-chart-fill-aca");
    const chartFillOnprem = document.getElementById("finops-chart-fill-onprem");

    if (barValAzure) barValAzure.textContent = `$${data.custo_azure_app_service.toFixed(2)}/mês`;
    if (barValAca) barValAca.textContent = `$${data.custo_azure_container_apps.toFixed(2)}/mês`;
    if (barValOnprem) barValOnprem.textContent = `$${data.custo_on_premise_estimado.toFixed(2)}/mês`;

    const maxCost = Math.max(
      data.custo_on_premise_estimado,
      data.custo_azure_app_service,
      data.custo_azure_container_apps,
      1
    );
    if (chartFillAzure) {
      chartFillAzure.style.width = `${Math.max(8, Math.round((data.custo_azure_app_service / maxCost) * 100))}%`;
    }
    if (chartFillAca) {
      chartFillAca.style.width = `${Math.max(8, Math.round((data.custo_azure_container_apps / maxCost) * 100))}%`;
    }
    if (chartFillOnprem) {
      chartFillOnprem.style.width = `${Math.max(8, Math.round((data.custo_on_premise_estimado / maxCost) * 100))}%`;
    }
  }

  function computeLocalFinOps(reqs, mem, inst, perfil) {
    const mult = { starter: 0.75, standard: 1.0, premium: 1.65 }[perfil] || 1.0;
    const fatorMem = Math.max(0, (mem - 512) / 512) * 3.5;

    const costAzure = (13.0 * mult + fatorMem) * inst + (reqs / 1000000) * 0.4;
    const costAca = Math.max(6.5, 8.5 * inst + (reqs / 1000000) * 0.85 + fatorMem * 0.6 * inst);
    const costOnprem = 45.0 * inst + 25.0 + fatorMem * 2.2 * inst;
    const savings = Math.max(0, ((costOnprem - costAzure) / costOnprem) * 100);
    const annual = Math.max(0, (costOnprem - costAzure) * 12);
    const rps = Math.max(50, Math.round((mem / 256) * 120 * inst));
    const latency = Math.max(6.5, 38.0 - inst * 3.5 - (perfil === "premium" ? 1.5 : 0));
    const vcpu = Number(Math.max(0.5, (mem / 1024) * inst).toFixed(1));

    let tierRec = "Basic / Standard (B1/S1 Linux)";
    let sla = "99.95%";
    if (inst >= 4 || reqs > 2000000 || mem >= 2048) {
      tierRec = "Premium v3 (P1v3 Auto-Scale)";
      sla = inst >= 2 ? "99.99%" : "99.95%";
    } else if (inst >= 2 || reqs >= 250000) {
      tierRec = "Standard (S1 Zone-Redundant)";
    }

    return {
      custo_azure_app_service: Number(costAzure.toFixed(2)),
      custo_azure_container_apps: Number(costAca.toFixed(2)),
      custo_on_premise_estimado: Number(costOnprem.toFixed(2)),
      economia_percentual: Number(savings.toFixed(1)),
      economia_anual_usd: Number(annual.toFixed(2)),
      sla_disponibilidade: sla,
      latencia_media_ms: Number(latency.toFixed(1)),
      requisicoes_suportadas_segundo: rps,
      tier_recomendado: tierRec,
      vcpu_alocada: vcpu,
    };
  }

  function updateFinOpsCalculations() {
    if (!sliderReqs || !sliderMem || !sliderInst) return;

    const reqs = parseInt(sliderReqs.value, 10);
    const mem = parseInt(sliderMem.value, 10);
    const inst = parseInt(sliderInst.value, 10);

    if (valReqs) valReqs.textContent = reqs.toLocaleString("pt-BR");
    if (valMem) valMem.textContent = `${mem} MB`;
    if (valInst) valInst.textContent = `${inst} nó${inst > 1 ? "s" : ""}`;

    const updateSliderFill = (slider, min, max, val) => {
      const pct = Math.min(100, Math.max(0, ((val - min) / (max - min)) * 100));
      slider.style.background = `linear-gradient(90deg, var(--azure) ${pct}%, var(--line) ${pct}%)`;
    };
    updateSliderFill(sliderReqs, 10000, 5000000, reqs);
    updateSliderFill(sliderMem, 256, 4096, mem);
    updateSliderFill(sliderInst, 1, 10, inst);

    const localData = computeLocalFinOps(reqs, mem, inst, activeFinopsProfile);
    applyFinOpsVisuals(localData);

    clearTimeout(finopsDebounceTimer);
    finopsDebounceTimer = setTimeout(async () => {
      try {
        const res = await fetch("/api/simulador/custos", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            requisicoes_mes: reqs,
            memoria_mb: mem,
            instancias: inst,
            perfil: activeFinopsProfile,
          }),
        });
        if (res.ok) {
          const remoteData = await res.json();
          applyFinOpsVisuals(remoteData);
        }
      } catch {}
    }, 180);
  }

  profileTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      profileTabs.forEach((t) => t.classList.remove("is-active"));
      tab.classList.add("is-active");
      activeFinopsProfile = tab.dataset.profile || "standard";
      updateFinOpsCalculations();
    });
  });

  finopsExportBtn?.addEventListener("click", () => {
    const report = {
      gerado_em: new Date().toISOString(),
      parametros: {
        perfil: activeFinopsProfile,
        requisicoes_mes: parseInt(sliderReqs?.value || "100000", 10),
        memoria_mb: parseInt(sliderMem?.value || "512", 10),
        instancias: parseInt(sliderInst?.value || "1", 10),
      },
      estimativa: lastFinopsResult,
    };
    navigator.clipboard.writeText(JSON.stringify(report, null, 2)).then(() => {
      showToast("Relatório FinOps JSON copiado para a área de transferência!", "success");
    });
  });

  sliderReqs?.addEventListener("input", updateFinOpsCalculations);
  sliderMem?.addEventListener("input", updateFinOpsCalculations);
  sliderInst?.addEventListener("input", updateFinOpsCalculations);
  updateFinOpsCalculations();

  const telemetryStatus = document.getElementById("telemetry-status");
  const telemetryUptime = document.getElementById("telemetry-uptime");
  const telemetryContacts = document.getElementById("telemetry-contacts");
  const telemetryDb = document.getElementById("telemetry-db");
  const telemetryDbSize = document.getElementById("telemetry-db-size");
  const telemetryReqsTotal = document.getElementById("telemetry-reqs-total");
  const telemetryPythonVer = document.getElementById("telemetry-python-ver");
  const telemetryAvgLatency = document.getElementById("telemetry-avg-latency");
  const telemetryRefreshBtn = document.getElementById("telemetry-refresh-btn");
  const heroLatencyVal = document.getElementById("hero-latency-val");
  const sparklineLine = document.getElementById("sparkline-line");
  const sparklineArea = document.getElementById("sparkline-area");

  function updateSparkline(samples) {
    if (!sparklineLine || !sparklineArea) return;
    const pts = Array.isArray(samples) && samples.length >= 2 ? samples : [3.2, 2.8, 2.5, 3.0, 2.2];
    const width = 300;
    const height = 54;
    const maxVal = Math.max(...pts, 10);
    const minVal = Math.min(...pts, 0);
    const range = Math.max(maxVal - minVal, 1);

    const coords = pts.map((val, idx) => {
      const x = Math.round((idx / (pts.length - 1)) * width);
      const y = Math.round(height - 8 - ((val - minVal) / range) * (height - 18));
      return `${x},${y}`;
    });

    const linePath = `M${coords.join(" L")}`;
    const areaPath = `M0,${height} L${coords.join(" L")} L${width},${height} Z`;
    sparklineLine.setAttribute("d", linePath);
    sparklineArea.setAttribute("d", areaPath);
  }

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
        if (telemetryDbSize && data.banco_tamanho_kb) {
          telemetryDbSize.textContent = `Volume SQLite: ${data.banco_tamanho_kb} KB`;
        }
        if (telemetryReqsTotal && typeof data.total_requisicoes === "number") {
          telemetryReqsTotal.textContent = `${data.total_requisicoes} reqs processadas`;
        }
        if (telemetryPythonVer && data.python_versao) {
          telemetryPythonVer.textContent = `FastAPI • Python ${data.python_versao}`;
        }
        if (telemetryAvgLatency) {
          telemetryAvgLatency.textContent = `~${data.latencia_media_ms || latency} ms`;
        }

        const seconds = Math.floor(data.uptime_segundos);
        const mins = Math.floor(seconds / 60);
        const hours = Math.floor(mins / 60);
        let uptimeStr = `${seconds}s`;
        if (hours > 0) uptimeStr = `${hours}h ${mins % 60}m`;
        else if (mins > 0) uptimeStr = `${mins}m ${seconds % 60}s`;

        if (telemetryUptime) telemetryUptime.textContent = uptimeStr;
        if (heroLatencyVal) heroLatencyVal.textContent = `~${latency} ms`;
        if (data.historico_latencia_ms) {
          updateSparkline(data.historico_latencia_ms);
        }
      }
    } catch {
      if (telemetryStatus) telemetryStatus.textContent = "Degradado";
    }
  }

  async function fetchRecentContacts() {
    const listContainer = document.getElementById("recent-contacts-list");
    if (!listContainer) return;

    try {
      const res = await fetch("/api/contatos/recentes?limite=4");
      if (!res.ok) return;
      const items = await res.json();

      if (!items.length) {
        listContainer.innerHTML = `<div class="recent-contact-empty">Nenhum protocolo registrado ainda. Envie o formulário ao lado para testar!</div>`;
        return;
      }

      listContainer.innerHTML = items
        .map(
          (item) => `
          <div class="recent-contact-item">
            <div class="recent-contact-top">
              <code class="protocol-pill">${escapeHtml(item.protocolo)}</code>
              <span class="topic-mini-badge">${escapeHtml(item.topico)}</span>
            </div>
            <div class="recent-contact-meta">
              <strong>${item.nome_mascarado}</strong>
              <span>(${escapeHtml(item.email_mascarado)})</span>
            </div>
          </div>
        `
        )
        .join("");
    } catch {}
  }

  telemetryRefreshBtn?.addEventListener("click", () => {
    fetchTelemetryMetrics();
    fetchRecentContacts();
    showToast("Métricas de telemetria atualizadas com sucesso.", "info");
  });

  fetchTelemetryMetrics();
  fetchRecentContacts();
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
      topicChips.forEach((c) => c.classList.remove("is-active"));
      chip.classList.add("is-active");
      const chosenTopic = chip.dataset.topic;
      if (topicInput && chosenTopic) topicInput.value = chosenTopic;
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
    contactForm.querySelectorAll("input, textarea").forEach((input) => {
      input.addEventListener("input", () => {
        input.classList.remove("is-invalid");
      });
    });

    contactForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const submitBtn = contactForm.querySelector('button[type="submit"]');
      const formData = new FormData(contactForm);
      const payload = Object.fromEntries(formData.entries());

      contactForm.querySelectorAll(".is-invalid").forEach((el) => el.classList.remove("is-invalid"));

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
          const parsedError = formatApiError(errData, contactForm);
          throw new Error(parsedError);
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
        fetchRecentContacts();
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

  function formatApiError(errData, formElement) {
    if (!errData) return "Verifique os campos preenchidos e tente novamente.";
    if (typeof errData.detail === "string") return errData.detail;

    if (Array.isArray(errData.detail)) {
      const fieldTranslations = {
        nome: "Nome Completo",
        email: "E-mail Profissional",
        mensagem: "Mensagem",
        topico: "Assunto",
      };

      const messages = errData.detail.map((err) => {
        const fieldKey = Array.isArray(err.loc) ? err.loc[err.loc.length - 1] : "";
        const fieldLabel = fieldTranslations[fieldKey] || fieldKey || "Campo";

        if (formElement && fieldKey) {
          const inputEl = formElement.querySelector(`[name="${fieldKey}"]`);
          if (inputEl) inputEl.classList.add("is-invalid");
        }

        if (err.type === "string_too_short") {
          const min = err.ctx?.min_length || 2;
          return `${fieldLabel} deve ter no mínimo ${min} caracteres`;
        }
        if (err.type === "string_too_long") {
          const max = err.ctx?.max_length || 1000;
          return `${fieldLabel} deve ter no máximo ${max} caracteres`;
        }
        if (err.type === "value_error" || err.type?.includes("email")) {
          return `${fieldLabel} informado é inválido`;
        }
        if (err.type === "missing") {
          return `${fieldLabel} é obrigatório`;
        }
        return `${fieldLabel}: preenchimento inválido`;
      });

      return messages.join(" • ");
    }

    return "Verifique os dados preenchidos e tente novamente.";
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

  function syntaxHighlight(json) {
    if (typeof json !== "string") {
      json = JSON.stringify(json, null, 2);
    }
    json = escapeHtml(json);
    return json.replace(
      /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
      (match) => {
        let cls = "json-number";
        if (/^"/.test(match)) {
          if (/:$/.test(match)) {
            cls = "json-key";
          } else {
            cls = "json-string";
          }
        } else if (/true|false/.test(match)) {
          cls = "json-boolean";
        } else if (/null/.test(match)) {
          cls = "json-null";
        }
        return `<span class="${cls}">${match}</span>`;
      }
    );
  }

  function renderUptimeHistory() {
    const container = document.getElementById("uptime-bars-track");
    if (!container) return;
    container.innerHTML = "";

    const today = new Date();
    for (let i = 29; i >= 0; i--) {
      const bar = document.createElement("div");
      bar.className = "uptime-bar-item";
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      const dateStr = date.toLocaleDateString("pt-BR", { day: "2-digit", month: "short" });
      const isToday = i === 0;
      const label = isToday ? `Hoje (${dateStr}): 100.0% Operacional` : `${dateStr}: 100.0% Operacional`;
      bar.title = label;
      bar.setAttribute("aria-label", label);
      container.appendChild(bar);
    }
  }
  renderUptimeHistory();

  const spotlightCards = document.querySelectorAll(
    ".feature, .service-card, .telemetry-card, .finops-controls-card, .finops-results-card, .arch-details-card, .cloud-card, .contact-form, .uptime-history-card, .recent-contacts-panel"
  );

  spotlightCards.forEach((card) => {
    card.addEventListener("mousemove", (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      card.style.setProperty("--mouse-x", `${x}px`);
      card.style.setProperty("--mouse-y", `${y}px`);
    });
  });

  const bottomNavItems = document.querySelectorAll(".mobile-bottom-item");
  if (bottomNavItems.length) {
    const sections = document.querySelectorAll("section[id]");
    window.addEventListener(
      "scroll",
      () => {
        let currentId = "";
        sections.forEach((sec) => {
          const top = sec.offsetTop - 200;
          if (window.scrollY >= top) {
            currentId = sec.getAttribute("id") || "";
          }
        });
        bottomNavItems.forEach((item) => {
          if (item.getAttribute("href") === `#${currentId}`) {
            item.classList.add("is-active");
          } else {
            item.classList.remove("is-active");
          }
        });
      },
      { passive: true }
    );
  }

  const windowGroups = document.querySelectorAll("[data-window-group]");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  if (windowGroups.length && !reduceMotion.matches && "IntersectionObserver" in window) {
    document.documentElement.classList.add("motion-enabled");

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );

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
