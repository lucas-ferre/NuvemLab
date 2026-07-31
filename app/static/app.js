const form = document.getElementById("contact-form");
const statusElement = document.getElementById("form-status");

function showStatus(message, state) {
  statusElement.textContent = message;
  statusElement.dataset.state = state;
}

if (form && statusElement) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const submitButton = form.querySelector('button[type="submit"]');
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());

    submitButton.disabled = true;
    showStatus("Enviando mensagem...", "loading");

    try {
      const response = await fetch("/api/contato", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error("A solicitação não pôde ser validada.");
      }

      const result = await response.json();
      form.reset();
      showStatus(`Mensagem recebida com sucesso. Protocolo #${result.id}.`, "success");
    } catch (error) {
      showStatus(error.message || "Falha no envio. Tente novamente.", "error");
    } finally {
      submitButton.disabled = false;
    }
  });
}

