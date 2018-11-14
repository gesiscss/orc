

$(document).ready(function() {
  $('.tabs__item').click(function() {
    $('.tabs__item.tabs__item--active').removeClass('tabs__item--active');
    $('.tabs__inner-content--active').removeClass('tabs__inner-content--active');

    $(this).addClass('tabs__item--active');
    var id = $(this).find('.tabs__link').attr('href');

    $(id).addClass('tabs__inner-content--active');
  })

  $('.tabs__link').click(function(e) {
    e.preventDefault();
  })
});

