// ===== Toggle material type fields (file vs link) in admin form =====
document.addEventListener('DOMContentLoaded', () => {
  const typeRadios = document.querySelectorAll('input[name="material_type"]');
  const fileField = document.getElementById('fileField');
  const linkField = document.getElementById('linkField');

  function updateFields() {
    const selected = document.querySelector('input[name="material_type"]:checked');
    if (!selected) return;

    if (selected.value === 'file') {
      fileField && fileField.classList.add('active');
      linkField && linkField.classList.remove('active');
    } else {
      linkField && linkField.classList.add('active');
      fileField && fileField.classList.remove('active');
    }
  }

  typeRadios.forEach(radio => radio.addEventListener('change', updateFields));
  if (typeRadios.length) updateFields();

  // Auto-hide flash messages after a few seconds
  document.querySelectorAll('.flash').forEach(flash => {
    setTimeout(() => {
      flash.style.transition = 'opacity 0.5s';
      flash.style.opacity = '0';
      setTimeout(() => flash.remove(), 500);
    }, 5000);
  });

  // Confirm before deleting
  document.querySelectorAll('.confirm-delete').forEach(form => {
    form.addEventListener('submit', (e) => {
      if (!confirm('Are you sure you want to delete this item?')) {
        e.preventDefault();
      }
    });
  });
});
