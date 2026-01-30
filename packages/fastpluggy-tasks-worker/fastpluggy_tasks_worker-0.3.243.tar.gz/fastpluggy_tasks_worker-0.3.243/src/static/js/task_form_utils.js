/**
 * Utilities for loading available tasks and updating the task form based on selection.
 * These functions rely on window.TASK_FORM_CONFIG:
 *   - url_list_available_tasks: string
 *   - availableTasks: array (filled after load)
 */

function updateTaskFormFromSelectionGeneric(selectId, paramsContainerId, topicInputId, existingArgs) {
  try {
    const selectEl = document.getElementById(selectId);
    if (!selectEl) return;

    const selected = selectEl.value;
    const taskMeta = (window.TASK_FORM_CONFIG?.availableTasks || []).find(t => t.name === selected);

    if (paramsContainerId) {
      if (taskMeta && taskMeta.params) {
        renderTaskForm(paramsContainerId, taskMeta.params);
        // Prefill values from existingArgs if provided
        if (existingArgs && typeof existingArgs === 'object') {
          try {
            Object.entries(existingArgs).forEach(([k, v]) => {
              const el = document.querySelector(`#${paramsContainerId} [name="${k}"]`);
              if (!el) return;
              if (el.type === 'checkbox') {
                el.checked = Boolean(v);
              } else {
                el.value = v;
              }
            });
          } catch (e) { /* ignore prefill errors */ }
        }
      } else {
        const container = document.getElementById(paramsContainerId);
        if (container) container.innerHTML = "<p class='text-muted'>No parameters required.</p>";
      }
    }

    if (topicInputId) {
      const topicInput = document.getElementById(topicInputId);
      if (topicInput) {
        const def = (taskMeta && taskMeta.topic) ? taskMeta.topic : "";
        topicInput.value = def || "";
      }
    }
  } catch (err) {
    console.error('updateTaskFormFromSelectionGeneric error', err);
  }
}

async function loadAvailableTasksGeneric(selectId, paramsContainerId, topicInputId, defaultSelected) {
  try {
    const url = window.global_var && window.global_var['url_list_available_tasks'];
    if (!url) {
      console.warn('No URL for available tasks. Expected window.global_var.url_list_available_tasks');
      return;
    }

    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch tasks');

    const tasks = await response.json();
    window.TASK_FORM_CONFIG = Object.assign({}, window.TASK_FORM_CONFIG, {
      availableTasks: tasks,
      defaultTask: tasks.length > 0 ? tasks[0].name : ''
    });

    renderTaskModuleFilters(tasks, selectId, paramsContainerId, topicInputId, defaultSelected);
    applyTaskFiltering(selectId, paramsContainerId, topicInputId, defaultSelected);

  } catch (error) {
    console.error('Error loading available tasks:', error);
  }
}

function renderTaskModuleFilters(tasks, selectId, paramsContainerId, topicInputId, defaultSelected) {
  const filterContainer = document.getElementById('task-module-filters');
  if (!filterContainer) return;

  const modules = [...new Set(tasks.map(t => t.module || 'unknown'))].sort();
  filterContainer.innerHTML = '';

  // Build tree structure
  const tree = {};
  modules.forEach(mod => {
    const parts = mod.split('.');
    let current = tree;
    parts.forEach((part, index) => {
      if (!current[part]) {
        current[part] = {
          fullPath: parts.slice(0, index + 1).join('.'),
          children: {}
        };
      }
      current = current[part].children;
    });
  });

  function renderTree(node, container, level = 0) {
    Object.keys(node).sort().forEach(key => {
      const item = node[key];
      const div = document.createElement('div');
      div.className = 'form-check';
      div.style.marginLeft = `${level * 1.2}rem`;
      
      const lsKey = `task_filter_mod_${item.fullPath}`;
      const checked = localStorage.getItem(lsKey) !== 'false';

      div.innerHTML = `
        <input class="form-check-input task-module-checkbox" type="checkbox" value="${item.fullPath}" id="chk-${item.fullPath}" 
               data-ls-key="${lsKey}" ${checked ? 'checked' : ''}>
        <label class="form-check-label" for="chk-${item.fullPath}">${key}</label>
      `;

      const input = div.querySelector('input');
      input.addEventListener('change', () => {
        // Cascading check/uncheck for children
        const allCheckboxes = filterContainer.querySelectorAll('.task-module-checkbox');
        allCheckboxes.forEach(childInput => {
          if (childInput.value.startsWith(item.fullPath + '.') || childInput.value === item.fullPath) {
            childInput.checked = input.checked;
            localStorage.setItem(childInput.getAttribute('data-ls-key'), input.checked);
          }
        });
        
        applyTaskFiltering(selectId, paramsContainerId, topicInputId, defaultSelected);
      });

      container.appendChild(div);
      renderTree(item.children, container, level + 1);
    });
  }

  renderTree(tree, filterContainer);
}

function applyTaskFiltering(selectId, paramsContainerId, topicInputId, defaultSelected) {
  const tasks = window.TASK_FORM_CONFIG?.availableTasks || [];
  
  // To handle the tree correctly, we look at the leaves (actual modules that exist in tasks)
  const filterCheckboxes = document.querySelectorAll('.task-module-checkbox');
  const modulesWithTasks = [...new Set(tasks.map(t => t.module || 'unknown'))];
  
  const activeModules = Array.from(filterCheckboxes)
    .filter(chk => chk.checked && modulesWithTasks.includes(chk.value))
    .map(chk => chk.value);

  const filteredTasks = tasks.filter(t => activeModules.includes(t.module || 'unknown'));

  // Group tasks by module/package
  const tasksByPackage = {};
  filteredTasks.forEach(task => {
    const pkg = task.module || 'unknown';
    if (!tasksByPackage[pkg]) tasksByPackage[pkg] = [];
    tasksByPackage[pkg].push(task);
  });

  const selectElement = document.getElementById(selectId);
  if (selectElement) {
    const wanted = defaultSelected || selectElement.value || window.TASK_FORM_CONFIG.defaultTask || '';
    selectElement.innerHTML = '';

    if (filteredTasks.length === 0) {
      const option = document.createElement('option');
      option.value = "";
      option.textContent = "No tasks match filters";
      selectElement.appendChild(option);
    } else {
      Object.entries(tasksByPackage).forEach(([pkg, pkgTasks]) => {
        const optgroup = document.createElement('optgroup');
        optgroup.label = pkg;
        pkgTasks.forEach(task => {
          const option = document.createElement('option');
          option.value = task.name;
          option.textContent = `${task.name} – ${task.description || task.qualified_name || ''}`;
          if (task.name === wanted) option.selected = true;
          optgroup.appendChild(option);
        });
        selectElement.appendChild(optgroup);
      });
    }
  }

  updateTaskFormFromSelectionGeneric(selectId, paramsContainerId, topicInputId);
}
