const projectList = document.getElementById('projectList');
const taskList = document.getElementById('taskList');
const taskForm = document.getElementById('taskForm');
const taskTitle = document.getElementById('taskTitle');
const taskDescription = document.getElementById('taskDescription');
const taskDue = document.getElementById('taskDue');
const taskPriority = document.getElementById('taskPriority');
const taskProject = document.getElementById('taskProject');
const activeProjectTitle = document.getElementById('activeProject');
const completedFilter = document.getElementById('completedFilter');
const dueBeforeInput = document.getElementById('dueBefore');
const searchInput = document.getElementById('searchInput');
const summaryEl = document.getElementById('summary');
const addProjectBtn = document.getElementById('addProjectBtn');
const projectDialog = document.getElementById('projectDialog');
const projectNameInput = document.getElementById('projectName');
const projectColorInput = document.getElementById('projectColor');
const projectDialogSubmit = document.getElementById('projectDialogSubmit');

let projects = [];
let activeProjectId = null;
let tasks = [];
let searchTimeout = null;

async function request(url, options = {}) {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    const message = detail.detail || 'Une erreur est survenue.';
    throw new Error(message);
  }
  if (response.status === 204) {
    return null;
  }
  return response.json();
}

async function loadProjects() {
  projects = await request('/api/projects');
  renderProjects();
  populateProjectSelect();
  if (activeProjectId === null && projects.length > 0) {
    const inbox = projects.find((project) => project.name === 'Inbox');
    activeProjectId = inbox ? inbox.id : projects[0].id;
  }
  setActiveProjectTitle();
}

async function loadTasks() {
  const params = new URLSearchParams();
  if (activeProjectId) {
    params.set('project_id', activeProjectId);
  }
  const filter = completedFilter.value;
  if (filter === 'active') {
    params.set('completed', 'false');
  } else if (filter === 'done') {
    params.set('completed', 'true');
  }
  if (dueBeforeInput.value) {
    params.set('due_before', dueBeforeInput.value);
  }
  if (searchInput.value.trim()) {
    params.set('search', searchInput.value.trim());
  }
  tasks = await request(`/api/tasks?${params.toString()}`);
  renderTasks();
  updateSummary();
}

function renderProjects() {
  projectList.innerHTML = '';
  projects.forEach((project) => {
    const item = document.createElement('li');
    item.className = 'project-item';
    if (project.id === activeProjectId) {
      item.classList.add('active');
    }
    item.dataset.projectId = project.id;

    const name = document.createElement('span');
    name.className = 'project-name';
    const color = document.createElement('span');
    color.className = 'color-dot';
    color.style.background = project.color;
    const label = document.createElement('span');
    label.textContent = project.name;
    name.append(color, label);
    item.appendChild(name);

    item.addEventListener('click', () => {
      activeProjectId = project.id;
      setActiveProjectTitle();
      loadTasks();
      renderProjects();
    });

    projectList.appendChild(item);
  });
}

function populateProjectSelect() {
  taskProject.innerHTML = '';
  const noneOption = document.createElement('option');
  noneOption.value = '';
  noneOption.textContent = 'Inbox';
  taskProject.appendChild(noneOption);
  projects.forEach((project) => {
    const option = document.createElement('option');
    option.value = project.id;
    option.textContent = project.name;
    if (project.id === activeProjectId) {
      option.selected = true;
    }
    taskProject.appendChild(option);
  });
}

function setActiveProjectTitle() {
  const project = projects.find((p) => p.id === activeProjectId);
  activeProjectTitle.textContent = project ? project.name : 'Inbox';
}

function renderTasks() {
  taskList.innerHTML = '';
  const template = document.getElementById('taskTemplate');
  if (tasks.length === 0) {
    const emptyState = document.createElement('li');
    emptyState.className = 'task-item';
    emptyState.textContent = 'Aucune tâche trouvée. Ajoutez-en une nouvelle !';
    taskList.appendChild(emptyState);
    return;
  }

  tasks.forEach((task) => {
    const node = template.content.firstElementChild.cloneNode(true);
    node.dataset.taskId = task.id;
    const checkbox = node.querySelector('.task-checkbox');
    checkbox.checked = task.completed;
    const title = node.querySelector('.task-title');
    title.textContent = task.title;
    const meta = node.querySelector('.task-meta');
    const metaItems = [];
    if (task.due_date) {
      metaItems.push(`<span class="tag">📅 ${formatDate(task.due_date)}</span>`);
    }
    metaItems.push(`<span class="tag">🔥 Priorité ${task.priority}</span>`);
    if (task.project_id) {
      const project = projects.find((p) => p.id === task.project_id);
      if (project) {
        metaItems.push(`<span class="tag" style="background:${hexToRgba(project.color)};color:${project.color}">📁 ${project.name}</span>`);
      }
    }
    if (task.description) {
      metaItems.push(`<span>${task.description}</span>`);
    }
    meta.innerHTML = metaItems.join('');

    if (task.completed) {
      node.classList.add('completed');
    }

    checkbox.addEventListener('change', () => toggleTask(task.id));
    node.querySelector('.delete-button').addEventListener('click', () => deleteTask(task.id));
    taskList.appendChild(node);
  });
}

function formatDate(value) {
  const date = new Date(value);
  return date.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' });
}

function hexToRgba(hex) {
  const parsed = hex.replace('#', '');
  const bigint = parseInt(parsed, 16);
  const r = (bigint >> 16) & 255;
  const g = (bigint >> 8) & 255;
  const b = bigint & 255;
  return `rgba(${r}, ${g}, ${b}, 0.18)`;
}

async function createTask(event) {
  event.preventDefault();
  const payload = {
    title: taskTitle.value.trim(),
    description: taskDescription.value.trim() || null,
    due_date: taskDue.value || null,
    priority: Number(taskPriority.value),
    project_id: taskProject.value ? Number(taskProject.value) : null,
  };
  if (!payload.title) {
    alert('Veuillez indiquer un titre.');
    return;
  }
  await request('/api/tasks', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  taskForm.reset();
  populateProjectSelect();
  await loadTasks();
}

async function toggleTask(taskId) {
  const updated = await request(`/api/tasks/${taskId}/toggle`, { method: 'PATCH' });
  tasks = tasks.map((task) => (task.id === taskId ? updated : task));
  renderTasks();
  updateSummary();
}

async function deleteTask(taskId) {
  if (!confirm('Supprimer cette tâche ?')) {
    return;
  }
  await request(`/api/tasks/${taskId}`, { method: 'DELETE' });
  tasks = tasks.filter((task) => task.id !== taskId);
  renderTasks();
  updateSummary();
}

function updateSummary() {
  request('/api/tasks/summary')
    .then((stats) => {
      summaryEl.innerHTML = `
        <span>📌 Total ${stats.total}</span>
        <span>✅ Terminées ${stats.completed}</span>
        <span>🚀 Actives ${stats.active}</span>
      `;
    })
    .catch(() => {
      summaryEl.textContent = 'Impossible de charger le résumé.';
    });
}

function handleProjectDialog() {
  projectDialog.addEventListener('close', async () => {
    if (projectDialog.returnValue !== 'confirm') {
      projectNameInput.value = '';
      return;
    }
    try {
      await request('/api/projects', {
        method: 'POST',
        body: JSON.stringify({
          name: projectNameInput.value.trim(),
          color: projectColorInput.value,
        }),
      });
      projectNameInput.value = '';
      await loadProjects();
      await loadTasks();
    } catch (error) {
      alert(error.message);
    }
  });

  addProjectBtn.addEventListener('click', () => {
    projectDialog.showModal();
    projectNameInput.focus();
  });

  projectDialogSubmit.addEventListener('click', (event) => {
    if (!projectNameInput.value.trim()) {
      event.preventDefault();
      alert('Veuillez indiquer un nom de projet.');
    }
  });
}

function registerFilters() {
  completedFilter.addEventListener('change', loadTasks);
  dueBeforeInput.addEventListener('change', loadTasks);
  searchInput.addEventListener('input', () => {
    window.clearTimeout(searchTimeout);
    searchTimeout = window.setTimeout(loadTasks, 300);
  });
}

async function init() {
  handleProjectDialog();
  registerFilters();
  taskForm.addEventListener('submit', createTask);
  await loadProjects();
  await loadTasks();
}

init().catch((error) => {
  console.error(error);
  alert('Impossible de charger Taskflow.');
});
