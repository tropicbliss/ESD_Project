// helper function to get datepicker title
const getDatePickerTitle = (elem) => {
  const label = elem.labels[0];
  return label ? label.textContent : elem.getAttribute('aria-label') || '';
};

// create a new Datepicker instance for each .datepicker_input element
document.querySelectorAll('.datepicker_input').forEach((elem) => {
  const datepicker = new Datepicker(elem, {
    format: 'dd/mm/yyyy', // UK format
    title: getDatePickerTitle(elem),
  });
});
