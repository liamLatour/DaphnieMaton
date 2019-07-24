var toggler = document.getElementsByClassName("caret");
var i;

for (i = 0; i < toggler.length; i++) {
  toggler[i].addEventListener("click", function () {
    this.parentElement.querySelector(".nested").classList.toggle("active");
    this.classList.toggle("caret-down");
  });
}

$(".sidenav a").on("click", function () {
  $.scrollify.move(getScrollifySectionIndex($(this).attr("href")));
});

//https://projects.lukehaas.me/scrollify/#home

$(function () {
  $.scrollify({
    section: ".sections",
    scrollbars: false,
    easing: "easeOutExpo",
    scrollSpeed: 1100,
    interstitialSection: ".header,.footer",
    before: function (i, panels) {
      //var ref = panels[i].attr("data-section-name");
      var ref = panels[i].attr("data-section-title");


      $(".sidenav .current").removeClass("current");
      $(".sidenav").find("a[href=\"#" + ref + "\"]").addClass("current");
      $(".sidenav").find("a[href=\"#" + ref + "\"]").parents().addClass("active");
      $(".sidenav").find("a[href=\"#" + ref + "\"]").parents().children(0).addClass("caret-down");

      if (ref == "overview") { //when going to overview
        console.log("start");
        $("#3dmodel").removeClass("hideImage");
        $("#3dmodel").addClass("animateImage");
      } else {
        $("#3dmodel").removeClass("animateImage");
        $("#3dmodel").addClass("hideImage");

        $target = panels[i];
        $target.removeClass('animateGrad');
        setTimeout("$target.addClass('animateGrad');", 100)
      }
    }
  });
});

$(".cable3").each(function () {
  gaine = $(this).attr("gaine");
  bout1 = $(this).attr("boutUn");
  bout2 = $(this).attr("boutDeux");
  bout3 = $(this).attr("boutTrois");
  $(this).html('<svg xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:cc="http://creativecommons.org/ns#"  xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"  xmlns:svg="http://www.w3.org/2000/svg" xmlns="http://www.w3.org/2000/svg" id="svg8"  version="1.1" viewBox="0 0 31.749998 10.583334" height="40" width="120">  <defs id="defs2" />  <metadata id="metadata5">      <rdf:RDF>          <cc:Work rdf:about="">              <dc:format>image/svg+xml</dc:format>              <dc:type rdf:resource="http://purl.org/dc/dcmitype/StillImage" />              <dc:title></dc:title>          </cc:Work>      </rdf:RDF>  </metadata>  <g transform="translate(0,-286.41664)" id="layer1">      <g transform="matrix(0.58741762,0,0,0.58741762,4.7025483,118.04358)" id="g910">          <rect              style="opacity:1;fill:' + gaine + ';fill-opacity:1;fill-rule:nonzero;stroke:none;stroke-width:0.30000001;stroke-linecap:round;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dasharray:none;stroke-dashoffset:0;stroke-opacity:1;paint-order:markers stroke fill"              id="rect815" width="25.513393" height="12.473214" x="-7.8596125" y="289.41763"              ry="0" />          <rect              style="opacity:1;fill:#ecd759;fill-opacity:1;fill-rule:nonzero;stroke:none;stroke-width:0.3271206;stroke-linecap:round;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dasharray:none;stroke-dashoffset:0;stroke-opacity:1;paint-order:markers stroke fill"              id="rect865" width="7.0625968" height="1.6370258" x="38.929119" y="288.91592" />          <rect              style="opacity:1;fill:#ecd759;fill-opacity:1;fill-rule:nonzero;stroke:none;stroke-width:0.3271206;stroke-linecap:round;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dasharray:none;stroke-dashoffset:0;stroke-opacity:1;paint-order:markers stroke fill"              id="rect865-2" width="7.0625968" height="1.6370258" x="38.929119"              y="294.83572" />         <rect              style="opacity:1;fill:#ecd759;fill-opacity:1;fill-rule:nonzero;stroke:none;stroke-width:0.3271206;stroke-linecap:round;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dasharray:none;stroke-dashoffset:0;stroke-opacity:1;paint-order:markers stroke fill"              id="rect865-4" width="7.0625968" height="1.6370258" x="38.929119"              y="300.66714" />          <path              style="fill:' + bout1 + ';fill-opacity:1;stroke:none;stroke-width:0.26458332px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1"              d="m 17.653781,289.41764 c 0,0 13.24886,-3.37695 21.90372,-1.62166 v 4.1105 c -10.82498,-0.73917 -21.90372,1.6689 -21.90372,1.6689 z"              id="path842-4-8" />          <path              style="fill:' + bout2 + ';fill-opacity:1;stroke:none;stroke-width:0.26458332px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1"              d="m 17.653781,297.73312 h 21.903722 v -4.15774 H 17.653781 Z" id="path842-3" />          <path              style="fill:' + bout3 + ';fill-opacity:1;stroke:none;stroke-width:0.26458332px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1"              d="m 17.653781,301.89086 c 0,0 13.248856,3.37695 21.903722,1.62166 v -4.1105 c -10.824984,0.73917 -21.903722,-1.6689 -21.903722,-1.6689 z"              id="path842-4" />      </g>  </g></svg>');
});

$(".cable4").each(function () {
  gaine = $(this).attr("gaine");
  bout1 = $(this).attr("boutUn");
  bout2 = $(this).attr("boutDeux");
  bout3 = $(this).attr("boutTrois");
  bout4 = $(this).attr("boutQuatre");
  $(this).html('<?xml version="1.0" encoding="UTF-8" standalone="no"?> <svg xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:cc="http://creativecommons.org/ns#" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:svg="http://www.w3.org/2000/svg" xmlns="http://www.w3.org/2000/svg" id="svg8" version="1.1" viewBox="0 0 31.749998 10.583334" height="40" width="120"> <defs id="defs2" /> <metadata id="metadata5"> <rdf:RDF> <cc:Work rdf:about=""> <dc:format>image/svg+xml</dc:format> <dc:type rdf:resource="http://purl.org/dc/dcmitype/StillImage" /> <dc:title></dc:title> </cc:Work> </rdf:RDF> </metadata> <g transform="translate(0,-286.41664)" id="layer1"> <g transform="translate(0.4209495)" id="g1505"> <rect style="opacity:1;fill:' + gaine + ';fill-opacity:1;fill-rule:nonzero;stroke:none;stroke-width:0.17622529;stroke-linecap:round;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dasharray:none;stroke-dashoffset:0;stroke-opacity:1;paint-order:markers stroke fill" id="rect815" width="14.987017" height="7.3269858" x="0.062287353" y="288.05261" ry="0" /> <g id="g1428" transform="translate(-0.396875,0.29557884)"> <rect y="287.00638" x="27.092991" height="1.0949285" width="4.148694" id="rect865" style="opacity:1;fill:#ecd759;fill-opacity:1;fill-rule:nonzero;stroke:none;stroke-width:0.20504373;stroke-linecap:round;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dasharray:none;stroke-dashoffset:0;stroke-opacity:1;paint-order:markers stroke fill" /> <rect y="289.58417" x="27.092991" height="1.0949285" width="4.148694" id="rect865-2" style="opacity:1;fill:#ecd759;fill-opacity:1;fill-rule:nonzero;stroke:none;stroke-width:0.20504373;stroke-linecap:round;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dasharray:none;stroke-dashoffset:0;stroke-opacity:1;paint-order:markers stroke fill" /> <rect y="292.16193" x="27.092991" height="1.0949285" width="4.148694" id="rect865-2-7" style="opacity:1;fill:#ecd759;fill-opacity:1;fill-rule:nonzero;stroke:none;stroke-width:0.20504373;stroke-linecap:round;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dasharray:none;stroke-dashoffset:0;stroke-opacity:1;paint-order:markers stroke fill" /> <rect y="294.73975" x="27.092991" height="1.0949285" width="4.148694" id="rect865-4" style="opacity:1;fill:#ecd759;fill-opacity:1;fill-rule:nonzero;stroke:none;stroke-width:0.20504373;stroke-linecap:round;stroke-linejoin:miter;stroke-miterlimit:4;stroke-dasharray:none;stroke-dashoffset:0;stroke-opacity:1;paint-order:markers stroke fill" /> </g> <path style="fill:' + bout4 + ';fill-opacity:1;stroke:none;stroke-width:0.1554209px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1" d="m 15.049304,295.37959 c 0,0 5.907293,1.34328 12.043687,1.03716 v -1.60965 c -6.195083,0.10679 -12.04369,-1.25926 -12.04369,-1.25926 z" id="path842-4" /> <path style="fill:' + bout2 + ';fill-opacity:1;stroke:none;stroke-width:0.15542091px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1" d="m 15.049304,291.71609 c 0,0 6.998151,-0.71835 12.043687,-0.49899 v -1.58875 c -5.111617,-0.40523 -12.043736,0.2564 -12.043736,0.2564 z" id="path842-3-6" /> <path id="path1439" d="m 15.049304,291.71609 c 0,0 6.998151,0.71835 12.043687,0.49899 v 1.58875 c -5.111617,0.40523 -12.043736,-0.2564 -12.043736,-0.2564 z" style="fill:' + bout3 + ';fill-opacity:1;stroke:none;stroke-width:0.15542091px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1" /> <path id="path1441" d="m 15.049304,288.05261 c 0,0 5.907293,-1.34328 12.043687,-1.03716 v 1.60965 c -6.195083,-0.10679 -12.04369,1.25926 -12.04369,1.25926 z" style="fill:' + bout1 + ';fill-opacity:1;stroke:none;stroke-width:0.1554209px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1" /> </g> </g> </svg>');
});

function getScrollifySectionIndex(anchor) {
  var idpanel = false;
  $('.sections').add($('.footer')).each(function (i) {
    if ($(this).data('section-title') == anchor.toString().replace(/#/g, "")) {
      idpanel = i;
    }
  });
  return idpanel;
};