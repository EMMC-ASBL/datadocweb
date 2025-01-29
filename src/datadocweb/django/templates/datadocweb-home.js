function onSearch() {
  let q = {
    graph: $('#graph').val(),
    query: $('#query').val(),
    fmt: 'json'
  };
  $.get("{% url 'datadocweb:home' %}", q, result => {
    console.log(result);
  }, 'json');
}