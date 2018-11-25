$(function() {

let lib_list = $('#lib_list')
  , lib_item_tpl = $('#lib_item_tpl')
  , elementInViewport = function(el) {
      var rect = el.getBoundingClientRect()
      return (
        rect.top    >= 0
        && rect.left   >= 0
        && rect.top <= (window.innerHeight || document.documentElement.clientHeight)
      )
    }
  , addEventListener = function(evt, fn) {
      window.addEventListener
        ? this.addEventListener(evt, fn, false)
        : (window.attachEvent)
          ? this.attachEvent('on' + evt, fn)
          : this['on' + evt] = fn;
    }
  , images = new Array()
  , loadImage = async function(el, fn) {
      let img = new Image()
        , src = await eel.load_work_image($(el).attr('data-src'))()
        ;
      img.onload = function() {
        $(el).attr('src', src);
        fn ? fn() : null;
      }
      img.src = src;
    }
  , processScroll = function() {
      for (var i = images.length-1; i >= 0; i--) {
        if (elementInViewport(images[i])) {
          loadImage(images[i]);
          images.splice(i, 1);
        }
      };
    }
  ;

lib_item_tpl.hide();

$('button.btn-open-url').click(function() {
  let e = $(this).parent().parent().find('input.form-control').first();
  let url = e.val();
  if (url) {
    eel.open_url(url);
  }
});

$('button.btn-copy').click(function() {
  let e = $(this).parent().parent().find('input.form-control').first();
  e.focus();
  e.select();
  document.execCommand('copy');
});

$('input.sel-on-focus').click(function() {
  $(this).select();
});

async function reload_library_root() {
  let v = await eel.get_library_root()();
  $('#text_library_root').val(v);
}

async function update_lib_list() {
  let list = await eel.get_lib()();
  lib_list.empty();
  images = [];
  if (list) {
    for (let i=0; i<list.length; ++i) {
      let e = lib_item_tpl.clone();
      let v = list[i];
      e.find('h3.title').text(v.rj);
      e.find('img').attr('data-src', v.image_path);
      e.find('div.op > a').click(function(e) {
        e.preventDefault();
      });
      e.show();
      lib_list.append(e);
      images.push(e.find('img')[0]);
    }
    processScroll();
  }
}

$('#text_library_root').change(async function() {
  let v = await eel.set_library_root($(this).val())();
  if(!v) {
    reload_library_root();
  }
});

$('#btn_refresh_library').click(async function() {
  let ok = await eel.refresh_library()();
  if (ok) {
    update_lib_list();
  }
});

reload_library_root();

processScroll();
addEventListener('scroll', processScroll);

});
