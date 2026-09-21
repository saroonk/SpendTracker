const accessToken = () => localStorage.getItem('accessToken');
const $ = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (accessToken()) headers.Authorization = `Bearer ${accessToken()}`;
  const response = await fetch(path, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(Object.values(data).flat().join(' ') || 'Request failed.');
  return data;
}

function showTracker(username = localStorage.getItem('username')) {
  $('login-section').classList.add('hidden');
  $('tracker-section').classList.remove('hidden');
  $('logout-button').classList.remove('hidden');
  $('welcome-message').textContent = `| Welcome, ${username || 'User'}`;
  $('date').value = new Date().toISOString().slice(0, 10);
  loadCategories();
  loadExpenses();
}

async function loadCategories() {
  const categories = await api('/api/categories/');
  const options = categories.map((item) => `<option value="${item.id}">${item.name}</option>`).join('');
  $('category').innerHTML = options;
  $('filter-category').innerHTML = '<option value="">All Categories</option>' + options;
}

async function loadExpenses(query = '') {
  const expenses = await api(`/api/expenses/${query}`);
  $('expense-count').textContent = `${expenses.length} ${expenses.length === 1 ? 'expense' : 'expenses'}`;
  $('expense-list').innerHTML = expenses.length ? `
    <div class="expense-table" role="table" aria-label="My expenses">
      <div class="expense-row expense-header" role="row">
        <span role="columnheader">Category</span><span role="columnheader">Amount</span><span role="columnheader">Note</span><span role="columnheader">Date</span>
      </div>
      ${expenses.map((expense) => `<div class="expense-row" role="row">
        <span class="expense-category" data-label="Category" role="cell">${expense.category_name}</span>
        <strong data-label="Amount" role="cell">₹${Number(expense.amount).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</strong>
        <span class="expense-note" data-label="Note" role="cell">${expense.note || '—'}</span>
        <span data-label="Date" role="cell">${expense.date}</span>
      </div>`).join('')}
    </div>` : '<div class="empty-state">No expenses yet.</div>';
}

async function loadSummary() {
  const summary = await api('/api/summary/');
  $('current-month-total').textContent = summary.current_month_total;
  $('previous-month-total').textContent = summary.previous_month_total;
  $('month-over-month').textContent = summary.month_over_month_percentage ?? 'N/A';
  $('summary-by-category').innerHTML = summary.current_month_by_category.length
    ? summary.current_month_by_category.map((item) => `<div><span>${item.category}</span><strong>${item.total}</strong></div>`).join('')
    : '<p class="muted">No spending this month.</p>';
  $('summary-insights').innerHTML = summary.insights.length
    ? summary.insights.map((insight) => `<div class="insight-card"><strong>${insight.category}</strong><span>${insight.message}</span></div>`).join('')
    : '<p class="muted">No category spending increased by more than 20% compared to last month.</p>';
}

$('view-summary-button').addEventListener('click', async () => {
  $('summary-section').classList.remove('hidden');
  try { await loadSummary(); }
  catch (error) { $('summary-by-category').textContent = error.message; }
});

$('close-summary-button').addEventListener('click', () => {
  $('summary-section').classList.add('hidden');
});

$('login-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    const data = await api('/api/auth/login/', { method: 'POST', body: JSON.stringify({ username: $('username').value, password: $('password').value }) });
    localStorage.setItem('accessToken', data.access);
    localStorage.setItem('refreshToken', data.refresh);
    localStorage.setItem('username', $('username').value);
    showTracker(localStorage.getItem(`firstName:${$('username').value}`) || $('username').value);
  } catch (error) { $('login-message').textContent = error.message; }
});

$('show-register-button').addEventListener('click', () => {
  $('login-section').classList.add('hidden');
  $('register-section').classList.remove('hidden');
  $('login-message').textContent = '';
});

$('show-login-button').addEventListener('click', () => {
  $('register-section').classList.add('hidden');
  $('login-section').classList.remove('hidden');
  $('register-message').textContent = '';
});

$('register-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const username = $('register-username').value.trim();
  const password = $('register-password').value;
  const confirmPassword = $('register-confirm-password').value;
  let message = '';

  if (!username) message = 'Username is required.';
  else if (!password) message = 'Password is required.';
  else if (!confirmPassword) message = 'Confirm password is required.';
  else if (password !== confirmPassword) message = 'Passwords do not match.';

  if (message) {
    $('register-message').textContent = message;
    return;
  }

  try {
    await api('/api/auth/register/', {
      method: 'POST',
      body: JSON.stringify({ first_name: $('register-first-name').value.trim(), last_name: $('register-last-name').value.trim(), username, password }),
    });
    localStorage.setItem(`firstName:${username}`, $('register-first-name').value.trim());
    $('register-form').reset();
    $('register-section').classList.add('hidden');
    $('login-section').classList.remove('hidden');
    $('login-message').textContent = 'Registration successful. Please log in.';
  } catch (error) { $('register-message').textContent = error.message; }
});

$('expense-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  if (Number($('amount').value) < 1) {
    $('expense-message').textContent = 'Amount must be at least ₹1.00.';
    return;
  }
  try {
    await api('/api/expenses/', { method: 'POST', body: JSON.stringify({ amount: $('amount').value, category: $('category').value, note: $('note').value, date: $('date').value }) });
    event.target.reset();
    $('date').value = new Date().toISOString().slice(0, 10);
    $('expense-message').textContent = 'Expense added.';
    await Promise.all([loadExpenses(), loadSummary()]);
  } catch (error) { $('expense-message').textContent = error.message; }
});

$('amount').addEventListener('invalid', () => {
  if (Number($('amount').value) < 1) $('expense-message').textContent = 'Amount must be at least ₹1.00.';
});

$('filter-button').addEventListener('click', async () => {
  const params = new URLSearchParams();
  if ($('filter-category').value) params.set('category', $('filter-category').value);
  if ($('start-date').value) params.set('start_date', $('start-date').value);
  if ($('end-date').value) params.set('end_date', $('end-date').value);
  try {
    await loadExpenses(params.toString() ? `?${params}` : '');
    $('filter-message').textContent = '';
  } catch (error) { $('filter-message').textContent = error.message; }
});

$('clear-filters-button').addEventListener('click', () => {
  $('filter-category').value = '';
  $('start-date').value = '';
  $('end-date').value = '';
  $('filter-message').textContent = '';
  loadExpenses();
});

$('logout-button').addEventListener('click', () => { localStorage.clear(); location.reload(); });
if (accessToken()) showTracker();