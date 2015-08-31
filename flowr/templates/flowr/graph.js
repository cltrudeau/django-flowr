var cy;

function updateBounds() {
  var bounds = cy.elements().boundingBox();
  $('#cy').css('height', bounds.h + 300);
  cy.center();
  cy.resize();
}

$(function() {
  $('#cy').cytoscape({
    panningEnabled: false,
    zoomingEnabled: false,
    style: [
      {
        selector: 'node',
        css: {
          'content': 'data(label)',
          'text-valign': 'center',
          'text-halign': 'center',
        }
      },
      {
        selector: 'edge',
        css: {
          'target-arrow-shape': 'triangle'
        }
      }
    ],
    elements: {{ graph | safe }},
    layout: {
      name: 'breadthfirst',
      directed: true,
      roots: {{ roots | safe}},
      padding: 5
    }
  });

  $(window).resize(function() {
    updateBounds();
  });

  // get cytoscapes controller instance
  cy = $('#cy').cytoscape('get');
  cy.on('ready', function(e) {
    updateBounds();
  });
});
