$(document).ready(function(){
    var w = $(window).width();
    $("#navbar").css("width",w);
    if(w<1010){
      $("#navbar").load("/navbar_adm");
      $("#sidebar").load("/sidebar_adm");
      $("#navbar").css("display","");
      $("#sidebar").css("display","none");
    }else{
      $("#navbar").load("/navbar_adm");
      $("#sidebar").load("/sidebar_adm");
      $("#navbar").css("display","none");
      $("#sidebar").css("display","");
    }
    $(window).resize(function() {
        w = $(window).width();
        $("#navbar").css("width",w);
        if(w<1010){
          $("#navbar").load("/navbar_adm");
          $("#sidebar").load("/sidebar_adm");
          $("#navbar").css("display","");
      $("#sidebar").css("display","none");
          }else{
          $("#navbar").load("/navbar_adm");
          $("#sidebar").load("/sidebar_adm"); 
          $("#navbar").css("display","none");
      $("#sidebar").css("display","");
          }
      });
  });