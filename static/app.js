const form = document.getElementById("job-form");
const jobsBody = document.getElementById("jobs-body");
const formTitle = document.getElementById("form-title");
const cancelBtn = document.getElementById("cancel-btn");

const fields = ["job-id", "title", "company", "location", "link", "salary", "status", "notes"];

function getFormData() {
  return {
    title: document.getElementById("title").value.trim(),
    company: document.getElementById("company").value.trim(),
    location: document.getElementById("location").value.trim() || null,
    link: document.getElementById("link").value.trim() || null,
    salary: document.getElementById("salary").value.trim() || null,
    status: document.getElementById("status").value,
    notes: document.getElementById("notes").value.trim() || null,
  };
}

function resetForm() {
  fields.forEach((id) => {
    const el = document.getElementById(id);
    if (!el) return;
    if (id === "status") el.value = "Applied";
    else el.value = "";
  });
  formTitle.textContent = "Add Job";
  cancelBtn.classList.add("hidden");
}

function escapeHtml(value = "") {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

async function loadJobs() {
  const res = await fetch("/api/jobs");
  const jobs = await res.json();

  jobsBody.innerHTML = jobs
    .map(
      (job) => `
      <tr>
        <td>${escapeHtml(job.title)}</td>
        <td>${escapeHtml(job.company)}</td>
        <td>${escapeHtml(job.location || "")}</td>
        <td>${job.link ? `<a href="${escapeHtml(job.link)}" target="_blank">View</a>` : ""}</td>
        <td>${escapeHtml(job.salary || "")}</td>
        <td>
          <select data-status-id="${job.id}">
            ${["Applied", "Interviewing", "Offer", "Rejected", "Accepted"]
              .map((s) => `<option ${job.status === s ? "selected" : ""}>${s}</option>`)
              .join("")}
          </select>
        </td>
        <td>${escapeHtml(job.notes || "")}</td>
        <td>
          <button data-edit-id="${job.id}">Edit</button>
          <button data-delete-id="${job.id}" class="danger">Delete</button>
        </td>
      </tr>`
    )
    .join("");
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("job-id").value;
  const payload = getFormData();

  const url = id ? `/api/jobs/${id}` : "/api/jobs";
  const method = id ? "PUT" : "POST";

  await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  resetForm();
  loadJobs();
});

cancelBtn.addEventListener("click", resetForm);

jobsBody.addEventListener("click", async (e) => {
  const editId = e.target.dataset.editId;
  const deleteId = e.target.dataset.deleteId;

  if (editId) {
    const res = await fetch(`/api/jobs/${editId}`);
    const job = await res.json();

    document.getElementById("job-id").value = job.id;
    document.getElementById("title").value = job.title;
    document.getElementById("company").value = job.company;
    document.getElementById("location").value = job.location || "";
    document.getElementById("link").value = job.link || "";
    document.getElementById("salary").value = job.salary || "";
    document.getElementById("status").value = job.status || "Applied";
    document.getElementById("notes").value = job.notes || "";

    formTitle.textContent = "Edit Job";
    cancelBtn.classList.remove("hidden");
  }

  if (deleteId) {
    if (!confirm("Delete this job?")) return;
    await fetch(`/api/jobs/${deleteId}`, { method: "DELETE" });
    loadJobs();
  }
});

jobsBody.addEventListener("change", async (e) => {
  const statusId = e.target.dataset.statusId;
  if (!statusId) return;

  const res = await fetch(`/api/jobs/${statusId}`);
  const job = await res.json();
  job.status = e.target.value;

  await fetch(`/api/jobs/${statusId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(job),
  });

  loadJobs();
});

loadJobs();
