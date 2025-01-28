function onReset() {
  $('#upload-database').prop('disabled', 'disabled').val('');
  $('#btn-database').text('Select database');
  $('#upload-data').val('');
  $('#upload-clipdata').val('');
  $('#upload-file').val('');
  $('#upload-clip').val('no data');
  $('#upload-delimiter').val('comma');
  $('#upload-header').val('1');
  $('#upload-rows').val('2');
  $('#upload-shape').val('no data');
  var form = $('#upload-form')[0];
  form.classList.remove('was-validated');
  form.classList.add('needs-validation');
  $('#upload-form').prop('novalidate', true);
  $('#upload-table thead').empty();
  $('#upload-table tbody').empty();
}
function onSelectDatabase(name) {
  if (name == '-new-') {
    $('#upload-database').prop('disabled', null).val('database.ttl');
    $('#btn-database').text('New database');  
  } else {
    $('#upload-database').prop('disabled', 'disabled').val(name);
    $('#btn-database').text(name.substring(0, 15) + '...');
  }
}
function delimiter_val(delimiter) {
  let choices = {
    comma: ',',
    semicolon: ';',
    tab: '\t',
    whitespace: 'null',
    colon: ':',
    pipe: '|'
  };
  if (delimiter) {
    Object.keys(choices).forEach(c => {
      if (delimiter == c) {
        $('#upload-delimiter').selectpicker('val', c);
      }
      else if (delimiter == choices[c]) {
        $('#upload-delimiter').selectpicker('val', c);
      }
    });
    $('#upload-delimiter').selectpicker('refresh');
  } else {
    let value = $('#upload-delimiter').val();
    return choices[value];
  }
}
function parseData(text, delimiter) {
  var cells = [];
  let lines = text.split('\n');
  if (lines.length > 0) {
    if (!delimiter) {
      let delimiters = [',', ';', '\t', ':', '|'];
      delimiter = 'null';
      for (let i = 0; i < delimiters.length; i++) {
        if (lines[0].indexOf(delimiters[i]) >= 0) {
          delimiter = delimiters[i];
          break;
        }
      }
      delimiter_val(delimiter);
    }
    if (delimiter == 'null') {
      cells = lines.map(x => x.split(/(\s+)/));
    } else {
      cells = lines.map(x => x.split(delimiter));
    }
  }
  return cells;
}
function trimChar(s, c) {
  let start = s.startsWith(c) ? c.length : 0;
  let stop = s.endsWith(c) ? s.length - c.length : s.length;
  return s.substring(start, stop);
}
function getHeader(cells) {
  let header = Number($('#upload-header').val());
  if (header <= 0)
    header = 1;
  header -= 1;
  var columns = [];
  if (header < cells.length) {
    columns = cells[header].map((item, i) => {
      let title = item.trim();
      if (title.length == 0)
        title = `Column${i + 1}`;
      let p1 = title.indexOf('[');
      let p2 = title.indexOf('(');
      let p = -1;
      if ((p1 > 0) && (p2 > 0)) {
        p = p1 < p2 ? p1 : p2;
      } else if (p2 > 0) {
        p = p2
      } else if (p1 > 0) {
        p = p1
      }
      var col = {};
      col.title = p > 0 ? title.substring(0, p).trim() : title;
      col.name = col.title.toLowerCase().replaceAll(' ', '_');
      var u1 = p > 0 ? title.substring(p + 1).trim() : '';
      col.unit = trimChar(trimChar(u1, ')'), ']');
      return col;
    });
  }
  return columns;
}
function getRows(cells, ncol) {
  var items = $('#upload-rows').val().split(',');
  var rows = new Set();
  items.forEach(item => {
    if (item.trim().length > 0) {
      let x = item.split('-').map(Number);
      if (x.length == 2) {
        let start = x[0] > 0 ? x[0] - 1 : 0;
        let stop = x[1] > 0 ? x[1] - 1 : 0;
        stop += 1;
        for (let r = start; r < stop; r++)
          rows.add(r);
      } else if (x.length == 1) {
        rows.add(x[0] > 0 ? x[0] - 1 : 0);
      }
    }
  });
  var data = [];
  var idx = Array.from(rows).filter(r => r < cells.length);
  idx.sort((a, b) => a - b);
  if (idx.length == 1) {
    for (let r = idx[0]; r < cells.length; r++) {
      if (cells[r].length == ncol)
        data.push(cells[r]);
    }
  } else {
    idx.forEach(r => {
      if (cells[r].length == ncol)
        data.push(cells[r]);
    });
  }
  return data;
}
function storeUploadData(cells) {
  $('#upload-shape').val('no data');
  var data = {};
  data.columns = getHeader(cells);
  let ncol = data.columns.length;
  data.rows = getRows(cells, ncol);
  let nrow = data.rows.length;
  console.log(data);
  if ((ncol >= 2) && (nrow > 0)) {
    var html = '';
    data.columns.forEach(c => {
      html += `<option value="${c.name}">${c.title}</option>`;
    });
    $('#upload-data').val(JSON.stringify(data));
    $('#upload-shape').val(`${nrow} rows, ${ncol} columns`);
    let head = data.columns.map(c => `<th>${c.title}</th>`).join('');
    $('#upload-table thead').empty().append(`<tr>${head}</td>`);
    let body = data.rows.map(row => {
      let cells = row.map(x => `<td>${x}</td>`).join('');
      return `<tr>${cells}</tr>`;
    });
    $('#upload-table tbody').empty().append(body.join(''));
  }
}
function readTextFile(delimiter) {
  let files = $('#upload-file')[0].files;
  if (files.length > 0) {
    let reader = new FileReader();
    reader.onload = function () {
      var cells = parseData(reader.result, delimiter);
      storeUploadData(cells);
    };
    reader.readAsText(files[0]);
  } else {
    var text = $('#upload-clipdata').val();
    if (text.length > 0) {
      var cells = parseData(text, delimiter);
      storeUploadData(cells);
    }
  }
}
function readExcelFile(sheet) {
  let files = $('#upload-file')[0].files;
  if (files.length > 0) {
    let reader = new FileReader();
    reader.onload = function () {
      let wb = XLSX.read(reader.result);
      if (!sheet) {
        sheet = wb.SheetNames[0]
        var html = '';
        wb.SheetNames.forEach(x => {
          html += `<option value="${x}">${x}</option>`;
        })
        $('#upload-sheet').empty().append(html);
        $('#upload-sheet').selectpicker('val', sheet);
        $('#upload-sheet').selectpicker('refresh');
      }
      let ws = wb.Sheets[sheet];
      var cells = XLSX.utils.sheet_to_json(ws, { header: 1 });
      storeUploadData(cells);
    };
    reader.readAsArrayBuffer(files[0]);
  }
}
function onFileChanged() {
  $('#upload-clipdata').val('');
  $('#upload-clip').val('no data');
  let file = $('#upload-file')[0].files[0];
  let fn = file.name.toLowerCase()
  if (fn.endsWith('.xlsx') || fn.endsWith('.xls')) {
    $('#ctrl-sheet').show();
    $('#ctrl-delimiter').hide();
    readExcelFile();
  } else {
    $('#ctrl-sheet').hide();
    $('#ctrl-delimiter').show();
    readTextFile();
  }
}
function onDelimiterChanged() {
  readTextFile(delimiter_val());
}
function onSheetChanged() {
  readExcelFile($('#upload-sheet').val());
}
function onReadFile() {
  if ($('#upload-sheet').is(':visible')) {
    onSheetChanged();
  }
  else if ($('#upload-delimiter').is(':visible')) {
    onDelimiterChanged();
  }
}
function onPasteData() {
  $('#upload-file').val('');
  $('#ctrl-sheet').hide();
  $('#ctrl-delimiter').show();
  $('#upload-clipdata').val('');
  $('#upload-clip').val('no data');
  navigator.clipboard.readText().then(text => {
    $('#upload-clipdata').val(text);
    let lines = text.split('\n');
    $('#upload-clip').val(`${lines.length} lines`);
    readTextFile();
    setFileAsRequired();
  });
}
function setFileAsRequired() {
  let filedata = $('#upload-data').val();
  $('#upload-file').prop('required', filedata ? null : true);
}
function onSubmit() {
  setFileAsRequired();
  $('#upload-database').prop('disabled', null);
  let form = $('#upload-form')[0];
  let valid = form.checkValidity();
  form.classList.add('was-validated');
  console.log('valid', valid);
  if (valid) {
    var prefix = {};
    let value = $('#upload-prefix').val();
    if (value) {
      value.split('\n').forEach(line => {
        let i = line.indexOf(':');
        if (i > 0) {
          let pr = line.substring(0, i).trim();
          let ns = line.substring(i+1).trim();
          prefix[pr] = ns;
        }      
      });
    }
    let data = {
      database: $('#upload-database').val(),
      filedata: $('#upload-data').val(),
      prefixes: JSON.stringify(prefix)
    };
    let csrftoken = form.csrfmiddlewaretoken.value;
    $('#btn-submit').html($('#submit-spinner').html()).prop('disabled', 'disabled');
    $('#btn-reset').prop('disabled', 'disabled');
    $.ajax({
      type: "POST",
      url: "{% url 'datadocweb:upload' %}",
      headers: { 'X-CSRFToken': csrftoken },
      dataType: 'json',
      data: data,
      success: function (result) {
        $('#btn-submit').text('Submit').prop('disabled', null);
        $('#btn-reset').prop('disabled', null);
        if (result.status == 'success') {
          $('#submit-success-text').text(`${result.nrow} rows inserted.`);
          $('#submit-error').hide();
          $('#submit-success').show();
        } else {
          $('#submit-error-text').text(result.error);
          $('#submit-success').hide();
          $('#submit-error').show();
        }
      }
    });
  }
}
