function showSearchError(sta, msg) {
  $('#search-status').remove();
  let ct = $('#search-error').html().trim()
           .replace('</strong>', '</strong> ' + msg)
           .replace('<div ', '<div id="search-status" ');
  $('#container').append(ct);
}
function onSearch() {
  let q = {
    graph: $('#graph').val(),
    query: $('#query').val(),
    fmt: 'json'
  };
  $('#search-status').remove();
  $('#search-result-none').hide();
  $('#search-how-to').hide();
  $('#search-result').hide();
  $('#search-spinner').show();
  $.get("{% url 'datadocweb:home' %}", q, result => {
    $('#search-spinner').hide();
    if (result.status == 'error') {
      showSearchError(result.error);
    }
    else if (result.status == 'success') {
      if (result.table.rows.length == 0) {
        $('#search-result-none').show();
      } else {
        let h = result.table.columns.map(c => `<th>${c}</th>`).join('');
        $('#result thead').empty().append(`<tr>${h}</tr>`);
        let j = result.table.columns.findIndex(c => c.endsWith('downloadURL'));
        let tr = result.table.rows.map(row => {
          let td = row.map((cell,i) => {
            let v = cell;
            if (j == i) {
              v = `<a href="${cell}" target="_blank">${cell}</a>`;
            }
            return `<td>${v}</td>`;
          });
          return `<tr>${td.join('')}</tr>`;
        });
        $('#result tbody').empty().append(tr.join(''));
        $('#search-result').show();
      }
    }
  }, 'json');
}