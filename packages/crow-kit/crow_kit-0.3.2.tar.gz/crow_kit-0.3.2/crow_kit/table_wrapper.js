window.userTasksCompleted = false;
window.inputFieldValues = [];
var panel_container_name = 'panel-container-auto-wrapper-x999999999990x0x0';
var popup_container = 'popup_container';
var panel_background_color = '#0d6efd';
var mouse_hover_background_color = '#ffc107';

var table_path = '';
var next_path = '';
var present_selection = '';

var basePanelTemplate = `

    <div class="st-actionContainer left-bottom">
	<div class="st-panel">
		<div class="st-panel-header"><i class="fa fa-bars" aria-hidden="true"></i> Wrapper Generation Panel - <b>Table</b></div>
		<div class="st-panel-contents" style="text-align:center;">
			
                        <button style="background-color: #dc3545 !important;margin-top:5px;" id="st_click" class="st_click"  >Select Table</button>
                        
                        <br><br>

                        <button  style="background-color: #dc3545 !important;margin-top:5px;" id="snp_click" class="snp_click"  >Select Next Page</button>

                        <br>
		</div>
		<div class="grid" style="text-align:center;">
                    
                    <button  style="cursor:pointer; width: 200px !important;background-color: #ccc !important;" class="doneBtn" >✔ Done</button>
				
                </div>
	</div>
	<div class="st-btn-container left-bottom">
		<div class="st-button-main"><i class="fa fa-bars" aria-hidden="true"></i></div>
	</div>
    </div>

`;

var panel = document.createElement('div');
panel.style.zIndex = '999999999';
panel.id = panel_container_name;

panel.insertAdjacentHTML('beforeend', basePanelTemplate);
document.body.appendChild(panel);

$(document).ready(function(){
    $('st-actionContainer').launchBtn( { openDuration: 500, closeDuration: 300 } );
});


document.addEventListener('mouseover', function (event) {
    var target = event.target;
    if (!isInjectedButton(target)) {
        target.style.backgroundColor = mouse_hover_background_color;
    }
});

document.addEventListener('mouseout', function (event) {
    var target = event.target;
    if (!isInjectedButton(target)) {
        target.style.backgroundColor = ''; // Reset background color when mouseout
    }
});

function getXPath(element) {
    var xpath = '';
    for (; element && element.nodeType === 1; element = element.parentNode) {
        var id = 1;
        for (var sibling = element.previousSibling; sibling; sibling = sibling.previousSibling) {
            if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                id++;
            }
        }
        id > 1 ? (id = '[' + id + ']') : (id = '');
        xpath = '/' + element.tagName.toLowerCase() + id + xpath;
    }
    
    // Use document.evaluate to get the text value using XPath
    var text = document.evaluate('string(' + xpath + ')', document, null, XPathResult.STRING_TYPE, null).stringValue;
    
    // Return both XPath and text value
    return { xpath: xpath, text: text.trim() };
}

function isInjectedButton(element) {
    var menuContainer = document.getElementById(panel_container_name);
    var popup_container_data = document.getElementById(popup_container);
    var sweetAlertContainer2 = document.getElementsByClassName('swal2-container');
    
    if(popup_container_data){
        if(menuContainer.contains(element) || popup_container_data.contains(element)){
            return true;
        }
    }else{
        if(menuContainer.contains(element)){
            return true;
        }
    }
  
    for (var i = 0; i < sweetAlertContainer2.length; i++) {
        if (sweetAlertContainer2[i].contains(element)) {
            return true;
        }
    }
    return false;
}

function generateRelativeClassNames(event) {
    selectClassNames = ''
    
    var hierarchy = [],
        current = event.srcElement || event.originalTarget;

    while (current.parentNode) {
        hierarchy.unshift(current);
        current = current.parentNode;
    }

    var xPathSegments = hierarchy.map(function (el) {
        return ((el.className !== '') ? '.' + el.className.split(' ').join('.') : '');
    });
    if(xPathSegments.length >0){
        selectClassNames =  xPathSegments[xPathSegments.length - 1];
    }
    
    return selectClassNames;
}


document.addEventListener('contextmenu', generateRelativeClassNames);

document.addEventListener('contextmenu', function (event) {
    
    var target = event.target;
    
    if (!isInjectedButton(target)) {
        
        var path = getXPath(target);
        
        if(present_selection == 'table_path'){
            table_path = path.xpath;
            //$( "#st" ).prop( "checked", true );
            $('.st_click').css('background-color', 'green');
            $('.st_click').css('color', 'white');
        }
        else if(present_selection == 'next_path'){
            next_path = path.xpath;
            //$( "#snp" ).prop( "checked", true );
            $('.snp_click').css('background-color', 'green');
            $('.snp_click').css('color', 'white');
        }
        
        event.preventDefault();
        
        return false;
    }
    
});

panel.querySelector('.st_click').addEventListener('click', function () {
    
    present_selection = 'table_path';

});

panel.querySelector('.snp_click').addEventListener('click', function () {
    present_selection = 'next_path';
});

//var doneButton = panel.querySelector('.doneBtn');
//doneButton.addEventListener('click', function () {
$(".st-actionContainer").on("click", ".doneBtn", function(event) {
    table_path = table_path.trim();
    if(table_path == ''){
        Swal.fire({
            icon: "info",
            text: "Please select which table you want to scrape."
        });
    }else{
        next_path = next_path.trim();
        if(next_path == ''){
            Swal.fire({
                title: "Are you sure?",
                text: "Do you need pagination data? If yes, please click select next page.",
                icon: "warning",
                showCancelButton: true,
                confirmButtonColor: "#3085d6",
                cancelButtonColor: "#d33",
                cancelButtonText: "No",
                confirmButtonText: "Yes, Need Pagination Data!"
              }).then((result) => {
                if (result.isConfirmed) {
                  
                }else{
                    dofinalOperation();
                }
              });
            
        }else{
           dofinalOperation();
        }
    }
});

function dofinalOperation(){ 

    var fieldValue = {
            table_path: table_path,
            next_path: next_path
        };
    window.inputFieldValues = []
    window.inputFieldValues.push(fieldValue);
    window.userTasksCompleted = true;
    
}