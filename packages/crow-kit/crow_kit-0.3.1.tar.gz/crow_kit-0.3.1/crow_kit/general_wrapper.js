
function uid() {
    var id = "id" + Math.random().toString(16).slice(2);
    return id;
}

window.userTasksCompleted = false;
window.inputFieldValues = [];
var panel_container_name = 'panel-container-auto-wrapper-x999999999990x0x0';
var popup_container = 'popup_container';
var panel_background_color = '#0d6efd';
var mouse_hover_background_color = '#ffc107';
var selectClassNames = '';
var selectIds = ''
var repeated_pattern_select = window.repeated_pattern

var table_path = '';
var next_path = '';
var parent_block = '';
var present_selection = '';
var clid = '';
var nowpid = '';

var basePanelTemplate = `

    <div class="st-actionContainer left-bottom">
	<div class="st-panel">
		<div class="st-panel-header"><i class="fa fa-bars" aria-hidden="true"></i> Wrapper Generation Panel - <b>General</b></div>
		<div class="st-panel-contents" style="max-height:200px;overflow:auto;">


                    <button style="background-color: #dc3545 !important;margin-top:5px;float: right !important;margin-left: 5px !important;"  id="spb_click" class="spb_click" >Select Parent Block</button>
                    <button style="background-color: #5bc0de !important;margin-top:5px;float: right !important;"  id="snp_click" class="snp_click" >Select Next Page</button>

                    
                    <div style="clear:both;"></div>
                    <div id="input_panel" style="margin-top:5px;">

                    </div>
                    <div id="button_panel1" style="margin-top:5px;">

                        <button type="button" style="float:right;background-color: green !important;float: right !important;" id="add_more">+ Add More</button> <br><br>
                          
                        <br>


                    </div>  

                
			
		</div>
		<div class="grid"  style="text-align:center;">

                    <button  style="cursor:pointer; width: 250px !important;background-color: #ccc !important;" class="doneBtn" >✔ Done</button>
				
                </div>
	</div>
	<div class="st-btn-container left-bottom">
		<div class="st-button-main"><i class="fa fa-bars" aria-hidden="true"></i></div>
	</div>
    </div>

`;

var htmlTemplate = `
    <div class="single_pair" style="padding:4px; position: relative;" id="field_panel_ID_">
        <input id="newAssetLiability_ID_key" style="color: black;" relId="_ID_" class="field_key_value field_key" placeholder="Select Attribute" name="newAssetLiability[_ID_][key]" type="text" />
        <input id="newAssetLiability_ID_value" style="color: black;" relId="_ID_" class="field_key_value field_value val_ID_" readonly placeholder="Select Value" name="newAssetLiability[_ID_][value]" type="text"/>
        <button pid="_ID_" style="color: white;background-color: green !important;" class="fields_verify_button fields_verify_button_ID_" >✔</button>
        <button pid="_ID_" class="fields_remove_button" style="color: white;background-color:red !important;position: absolute; right: 4px; top: 50%; transform: translateY(-50%); cursor: pointer;">✖</button>
    </div>
`;


var panel = document.createElement('div');
panel.style.zIndex = '999999999';
panel.id = panel_container_name;



$('body').on('click', '.field_key_value', function (e) {
    clid = $(this).attr('id');
    nowpid = $(this).attr('relId');
    present_selection = '';
});

panel.insertAdjacentHTML('beforeend', basePanelTemplate);



var inputPanel = panel.querySelector('#input_panel');
// Append htmlTemplate under the input_panel div

var cloned_html = htmlTemplate;

var uid = uid();
cloned_html = cloned_html.replace(/_ID_/g, uid);
inputPanel.insertAdjacentHTML('beforeend', cloned_html);
document.body.appendChild(panel);

var addButton = panel.querySelector('#add_more');
addButton.addEventListener('click', function () {
    // Append htmlTemplate when the button is clicked
    var cloned_html = htmlTemplate;
    var uid = "id" + Math.random().toString(16).slice(2);
    cloned_html = cloned_html.replace(/_ID_/g, uid);
    inputPanel.insertAdjacentHTML('beforeend', cloned_html);
});

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

function generateRelativeClassAndIdNames(event) {
    selectClassNames = '';
    selectIds = '';

    var hierarchy = [],
        current = event.srcElement || event.originalTarget;

    while (current.parentNode) {
        hierarchy.unshift(current);
        current = current.parentNode;
    }

    var xPathSegments = hierarchy.map(function (el) {
        var className = (el.className !== '') ? '.' + el.className.split(' ').join('.') : '';
        var id = (el.id !== '') ? '#' + el.id : '';
        return className + id;
    });

    if (xPathSegments.length > 0) {
        selectClassNames = xPathSegments[xPathSegments.length - 1];
        selectIds = xPathSegments[xPathSegments.length - 1];
    }

    return {
        classNames: selectClassNames,
        ids: selectIds
    };
}


if(repeated_pattern_select != 'yes'){  
 $('#spb_click').attr('style', 'display: none !important');
}


document.addEventListener('contextmenu', generateRelativeClassNames);

document.addEventListener('contextmenu', function (event) {
    var target = event.target;
    if (!isInjectedButton(target)) {
        var path = getXPath(target);
        if(present_selection == 'next_path'){
            next_path = path.xpath;
        }else if(present_selection == 'parent_block'){
            parent_block = selectClassNames;
        }else{     
            if(clid != ''){

                if(clid.includes('key')){
                    $('#'+clid).val(path.text);
                }else{
                    if(repeated_pattern_select=='yes'){
                        $('#'+clid).val(selectClassNames);
                    }else{
                        //Swal.fire(clid + '2' + path.xpath);
                        $('#'+clid).val(path.xpath);
                    }
                }
            }
        }
        event.preventDefault();
        return false;
    }
});


$('body').on('click', '.fields_verify_button', function (e) {
    pid = $(this).attr('pid');
    nowpid = pid;
    attMane = $('#newAssetLiability' + pid + 'key').val();
    bclass = parent_block;
    cclass = $('#newAssetLiability' + pid + 'value').val();
    var innermostText = '';
    b = 0;
    
    
    
    if(repeated_pattern_select !='yes'){
        Swal.fire(pid + repeated_pattern_select);
        if(cclass == '' || attMane == ''){
            
            Swal.fire({
                text: "Please select attribute and value both!",
                icon: "info"
            });
            
            return false;
            
        }else{
            var resultpath = document.evaluate(cclass, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
            if (resultpath.singleNodeValue) {
                foundElement = resultpath.singleNodeValue;
                innermostText = foundElement.textContent;
            }else{
                innermostText = '';
            }
        }
        
    }else{
        parent_block = parent_block.trim();
        if(parent_block==''){
            
            Swal.fire({
                text: "Please select parent block!",
                icon: "info"
            });
            return false;
            
        }else if(cclass == '' || attMane == ''){
            
            Swal.fire({
                text: "Please select attribute and value both!",
                icon: "info"
            });
            
            return false;
            
        }else{
            $(bclass).each(function () {
                if(b<5){
                    innermostText = innermostText + $(this).find(cclass).text() + '\n';
                }
                b = b + 1;
            });
        }
    }
    
    Swal.fire({
        title: "Is the following sample data collection correct based on your selection?",
        text: innermostText,
        icon: "info",
        showCancelButton: true,
        confirmButtonColor: "#d33",
        cancelButtonColor: "#3085d6",
        confirmButtonText: "No",
        cancelButtonText: "Yes",
    }).then((result) => {
      if (result.isConfirmed) {
        Swal.fire({
          text: "Let\'s try again by diiferent way!",
          icon: "info"
        });
      }
    });
});

panel.querySelector('.snp_click').addEventListener('click', function () {
  
    present_selection = 'next_path';
});

panel.querySelector('.spb_click').addEventListener('click', function () {
  
    present_selection = 'parent_block';
});


$('body').on('click', '.fields_remove_button', function (e) {
    pid = $(this).attr('pid');
    $('#field_panel'+pid).remove();
});

//var doneButton = panel.querySelector('.doneBtn');
//doneButton.addEventListener('click', function () {
$(".st-actionContainer").on("click", ".doneBtn", function(event) {    
    inputFieldValuesInner = [];
    invalid_data = false;
    
   
    var allPairs = document.querySelectorAll('.single_pair');
    if(allPairs.length == 0){
        invalid_data = true;
    }
    allPairs.forEach(function(pairElement) {
        // Get key and value for each pair
        var keyInput = pairElement.querySelector('.field_key');
        var valueInput = pairElement.querySelector('.field_value');
        
        keyInput = keyInput.value;
        valueInput = valueInput.value;
        keyInput = $.trim(keyInput);
        valueInput = $.trim(valueInput);
        
        
        if(keyInput == '' || valueInput == ''){
                invalid_data = true;
        }
   
        var fieldValue = {
            attribute_name: keyInput,
            attribute_value: valueInput
        };
        inputFieldValuesInner.push(fieldValue);
    });
    
    var fieldValue = {
            data_fields: inputFieldValuesInner,
            next_path: next_path,
            parent_path: parent_block,
    };
    
    if(invalid_data){
        Swal.fire({
            icon: "error",
            title: "Oops...",
            text: "Please select attributes and values(with parents).!",
        });
    }else{
        next_path = next_path.trim();
        parent_block = parent_block.trim();
        
        if(repeated_pattern_select == 'yes'){  
            if(parent_block==''){

                Swal.fire({
                    text: "Please select parent block!",
                    icon: "info"
                });
                return false;

            }
        }
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
                    window.userTasksCompleted = true;
                    window.inputFieldValues.push(fieldValue);   
                }
              });
            
        }else{
            window.userTasksCompleted = true;
            window.inputFieldValues.push(fieldValue);
        }
    }
    
});