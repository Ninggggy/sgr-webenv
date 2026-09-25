const FormUtil = {
    getVal: id => document.querySelector(`#${id}`)?.value,
    isChecked: id => $(`#${id}`).is(':checked'),
    isEnabled: id => $(`#${id}`).is(':enabled'),
    getRadioVal: name => $(`input[name="${name}"]:checked`).val() || null
};

export default FormUtil;
