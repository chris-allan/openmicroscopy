/*
 * Copyright (c) 2008-2011 University of Dundee. & Open Microscopy Environment.
 * All rights reserved.
 * 
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 * 
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 * 
 * Author: Aleksandra Tarkowska <A(dot)Tarkowska(at)dundee(dot)ac(dot)uk>, 2008.
 */

String.prototype.capitalize = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
}

jQuery.fn.alternateRowColors = function() {
    var $rows = $(this).children().children('tr');
    $rows.not('.hidden').filter(':odd').removeClass('even').addClass('odd');
    $rows.not('.hidden').filter(':even').removeClass('odd').addClass('even');
  return this;
}

function openPopup(url) {
    // IE8 doesn't support arbitrary text for 'name' 2nd arg.  #6118
    var owindow = window.open(url, '', config='height=600,width=850,left=50,top=50,toolbar=no,menubar=no,scrollbars=yes,resizable=yes,location=no,directories=no,status=no');
    if(!owindow.closed) owindow.focus();
    return false;
}


function openCenteredWindow(url) {
    var width = 550;
    var height = 600;
    var left = parseInt((screen.availWidth/2) - (width/2));
    var top = 0 // parseInt((screen.availHeight/2) - (height/2));
    var windowFeatures = "width=" + width + ",height=" + height + ",status=no,resizable=yes,scrollbars=yes,menubar=no,toolbar=no,left=" + left + ",top=" + top + "screenX=" + left + ",screenY=" + top;
    var myWindow = window.open(url, "", windowFeatures);
    if(!myWindow.closed) myWindow.focus();
    return false;
}


/*
 *  Returns a string representing the currently selected items in the $.jstree.
 * E.g.     "Image=23,34,98&Dataset=678"
**/
function get_tree_selection() {
    if (typeof $.jstree == "undefined") return "";
    var datatree = $.jstree._focused();

    var ids = new Array();
    var Data_Type = null;
    var selected = datatree.data.ui.selected;
    if (selected.size() == 1) {
        var klass = selected.attr('rel');
        if (klass == 'plate' || klass == 'acquisition') {
            var plateSelected = $('#spw .ui-selected img');
            if (plateSelected.size() > 0) {
                selected = plateSelected;
            }
        }
    }
    var selected_ids = {}
    selected.each(function() {
        var dtype = this.id.split("-")[0];
        var data_type = dtype.charAt(0).toUpperCase() + dtype.slice(1); // capitalise
        var data_id = this.id.split("-")[1];
        if (data_type in selected_ids) {
            selected_ids[data_type] += ","+data_id;
        } else {
            selected_ids[data_type] = data_id
        }
    });
    var ids_list = []
    for (key in selected_ids){
        ids_list.push(key+"="+selected_ids[key]);
    }
    return ids_list.join("&");
}


/*
 * Confirm dialog using jquery-ui dialog. http://jqueryui.com/demos/dialog/
 * This code provides a short-cut that doens't need html elements on the page
 * Basic usage (text only - Default buttons are 'OK' and 'Cancel'):
 *    var OK_dialog = confirm_dialog("Can you confirm that you want to proceed?", function() {
 *        var clicked_button_text = OK_dialog.data("clicked_button");
 *        alert(clicked_button_text);
 *    });
 *
 * Also possible to specify title, buttons, width, height:
 *    var btn_labels = ["Yes", "No", "Maybe", "Later"];
 *    var title_dialog = confirm_dialog("Can you confirm that you want to proceed?", 
 *          function() { alert( title_dialog.data("clicked_button") },
 *          "Dialog Title", btn_labels, 300, 200);
 */
var confirm_dialog = function(dialog_text, callback, title, button_labels, width, height) {

    if ((typeof title == "undefined") || (title === null)) var title = "Confirm";
    if ((typeof width == "undefined") || (width === null)) var width = 350;
    if ((typeof height == "undefined") || (height === null)) var height = 140;

    var $dialog = $("#confirm_dialog");
    if ($dialog.length > 0) {       // get rid of any old dialogs
        $dialog.remove();
    }
    $dialog = $("<div id='confirm_dialog'></div>");
    $('body').append($dialog);

    $dialog.attr("title", title).hide();
    $dialog.html("<p>"+ dialog_text +"</p>");

    if (typeof button_labels == "undefined") {
        button_labels = ['OK', 'Cancel']
    }
    var btns = {}
    for (var i=0; i<button_labels.length; i++) {
        var b = button_labels[i];
        btns[b] = function(event) {
            var btxt = $(event.target).text();
            $dialog.data("clicked_button", btxt);
            $( this ).dialog( "close" );
        }
    }

    $dialog.dialog({
        resizable: true,
        height: height,
        width: width,
        modal: true,
        buttons: btns
    });
    $dialog.bind("dialogclose", callback);

    return $dialog;
};


/*
 * A dialog for sending feedback. 
 * Loads and submits the feedback form at "/feedback/feedback"
 */
var feedback_dialog = function(error) {

    var $feedback_dialog = $("#feedback_dialog");
    if ($feedback_dialog.length > 0) {       // get rid of any old dialogs
        $feedback_dialog.remove();
    }
    $feedback_dialog = $("<div id='feedback_dialog'></div>");
    $('body').append($feedback_dialog);

    $feedback_dialog.attr("title", "Send Feedback").hide();
    $feedback_dialog.load("/feedback/feedback #form-500", function() {
        $("textarea[name=error]", $feedback_dialog).val(error);
        $("input[type=submit]", $feedback_dialog).hide();
        $("form", $feedback_dialog).ajaxForm({
            success: function(data) {
                $feedback_dialog.html(data);
                $feedback_dialog.dialog("option", "buttons", {
                    "Close": function() {
                        $( this ).dialog( "close" );
                    }
                });
            }
        });
    });

    $feedback_dialog.dialog({
        resizable: true,
        height: 500,
        width: 700,
        modal: true,
        buttons: {
            "Cancel": function() {
                $( this ).dialog( "close" );
            },
            "Send": function() {
                $("form", $feedback_dialog).submit();
            }
        }
    });
    return $feedback_dialog;
};

/** 
 * Handle jQuery load() errors (E.g. timeout)
 * In this case we simply refresh (will redirect to login page)
**/
$(document).ready(function(){
    $("body").ajaxError(function(e, req, settings, exception) {
        if (req.status == 404) {
            var msg = "Url: " + settings.url + "<br/>" + req.responseText;
            confirm_dialog(msg, null, "404 Error", ["OK"], 360, 200);
        } else if (req.status == 403) {
            // Denied (E.g. session timeout) Refresh - will redirect to login page
            window.location.reload();
        } else if (req.status == 500) {
            // Our 500 handler returns only the stack-trace if request.is_json()
            var error = req.responseText;
            feedback_dialog(error);
        }
    });
});


/*
 * NB: This code is NOT USED currently. Experimental.
 * A dialog for logging-in on the fly (without redirect to login page).
 * On clicking 'Connect' we post username & password to login url and on callback, the callback function is called
 */
var login_dialog = function(login_url, callback) {

    var $dialog = $("#login_dialog");
    if ($dialog.length > 0) {       // get rid of any old dialogs
        $dialog.remove();
    }
    $dialog = $("<div id='login_dialog'></div>");
    $('body').append($dialog);

    $dialog.attr("title", "Login").hide();
    $dialog.html("<form>Username:<input type='text' name='username' id='login_username' /><br />Password:<input type='text' name='password' id='login_password'/>");

    $dialog.dialog({
        resizable: true,
        height: 200,
        width: 300,
        modal: true,
        buttons: {
            "Cancel": function() {
                $( this ).dialog( "close" );
            },
            "Connect": function() {
                var username = $("#login_username").val();
                var password = $("#login_password").val();
                $.post(login_url, {'password':password, 'username':username, 'noredirect':'true'},  function(data) {
                    //console.log("logged-in...");
                    callback();
                });
                $( this ).dialog( "close" );
            }
        }
    });
    $dialog.bind("dialogclose", callback);

    return $dialog;
};


(function ($) {

    // This jQuery plugin is used to init a right-panel webclient-plugin (too many plugins!)
    // It adds listeners to selection and tab-change events, updating the panel by loading 
    // a url based on the currently selected objects.
    // Example usage:
    //
    //  $("#rotation_3d_tab").omeroweb_right_plugin({           // The tab content element
    //      plugin_index: 3,                                    // The tab index
    //      load_tab_content: function(selected, obj_dtype, obj_id) {    // Url based on selected object(s)
    //          $(this).load('{% url weblabs_index %}rotation_3d_viewer/'+obj_id);
    //      },
    //      supported_obj_types: ['image','dataset'],   // E.g. only support single image/dataset selected
    //  });
    $.fn.omeroweb_right_plugin = function (settings) {

        returnValue = this;

        // Process each jQuery object in array
        this.each(function(i) {
            // 'this' is the element we're working with
            var $this = $(this);

            // store settings
            var plugin_tab_index = settings['plugin_index'],
                load_tab_content = settings['load_tab_content'],
                supported_obj_types = settings['supported_obj_types'],
                tab_enabled = settings['tab_enabled'];      // only used if 'supported_obj_types' undefined

            var update_tab_content = function() {
                // get the selected id etc
                var selected = $("body").data("selected_objects.ome");
                if (selected.length == 0) {
                    return;
                }
                var obj_id = selected[0]['id'];     // E.g. image-123
                var dtype = obj_id.split("-")[0];    // E.g. 'image'
                var oid = obj_id.split("-")[1];

                // if the tab is visible and not loaded yet...
                if ($this.is(":visible") && $this.is(":empty")) {
                    // we want the context of load_tab_content to be $this
                    $.proxy(load_tab_content,$this)(selected, dtype, oid);
                };
            };

            // update tabs when tree selection changes or tabs switch
            $("#annotation_tabs").bind( "tabsshow", function(tab_ui, tab){
                if (tab.index == plugin_tab_index) {
                    $this.show();   // sometimes this doesn't get shown until too late
                    update_tab_content();
                }
            });

            // on change of selection in tree, update which tabs are enabled
            $("body").bind("selection_change.ome", function(event) {

                // clear contents of panel
                $this.empty();

                // get selected objects
                var selected = $("body").data("selected_objects.ome");
                if (selected.length == 0) {
                    $("#annotation_tabs").tabs("disable", plugin_tab_index);
                    return;
                }
                var obj_id = selected[0]['id'];     // E.g. image-123
                var orel = obj_id.split("-")[0];    // E.g. 'image'

                // we only care about changing selection if this tab is selected...
                var select_tab = $("#annotation_tabs").tabs( "option", "selected" );
                var supported;
                if (typeof supported_obj_types != 'undefined') {
                    supported = ($.inArray(orel, supported_obj_types) >-1) && (selected.length == 1);
                } else { 
                    supported = tab_enabled(selected);
                }

                // update enabled & selected state
                if(!supported) {
                    $("#annotation_tabs").tabs("disable", plugin_tab_index);
                    if (plugin_tab_index == select_tab) {
                        // if we're currently selected - switch to first tab
                        $("#annotation_tabs").tabs("select", 0);
                    }
                } else {
                    $("#annotation_tabs").tabs("enable", plugin_tab_index);
                    // update tab content
                    update_tab_content();
                }
            });

        });
        // return the jquery selection (or if it was a method call that returned a value - the returned value)
        return returnValue;
    };


    // This plugin is similar to the one above, handling center-panel webclient-plugin init.
    $.fn.omeroweb_center_plugin = function (settings) {

        returnValue = this;

        // Process each jQuery object in array
        this.each(function(i) {
            // 'this' is the element we're working with
            var $this = $(this);

            // store settings
            var plugin_index = settings['plugin_index'],
                load_plugin_content = settings['load_plugin_content'],
                supported_obj_types = settings['supported_obj_types'],
                plugin_enabled = settings['plugin_enabled'],      // only used if 'supported_obj_types' undefined
                empty_on_sel_change = settings['empty_on_sel_change'];
            if (typeof empty_on_sel_change == 'undefined') empty_on_sel_change = true;  // TODO use default settings

            var update_plugin_content = function() {
                // get the selected id etc
                var selected = $("body").data("selected_objects.ome");
                if (selected.length == 0) {
                    return;
                }
                var obj_id = selected[0]['id'];     // E.g. image-123
                var dtype = obj_id.split("-")[0];    // E.g. 'image'
                var oid = obj_id.split("-")[1];

                // if the tab is visible...
                if ($this.is(":visible")) {
                    // we want the context of load_plugin_content to be $this
                    $.proxy(load_plugin_content,$this)(selected, dtype, oid);
                };
            };


            $('#center_panel_chooser').bind('center_plugin_changed.ome', update_plugin_content);

            // on change of selection in tree, update which tabs are enabled
            $("body").bind("selection_change.ome", function(event) {

                // clear contents of panel
                if (empty_on_sel_change) {
                    $this.empty();
                }

                // get selected objects
                var selected = $("body").data("selected_objects.ome");
                if (selected.length == 0) {
                    set_center_plugin_enabled(plugin_index, false);
                    return;
                }
                var obj_id = selected[0]['id'];     // E.g. image-123
                var orel = obj_id.split("-")[0];    // E.g. 'image'

                // do we support the data currently selected?
                var supported;
                if (typeof supported_obj_types != 'undefined') {
                    // simply test E.g. if "image" is in the supported types
                    supported = ($.inArray(orel, supported_obj_types) >-1) && (selected.length == 1);
                } else {
                    // OR use the user-specified function to check support
                    supported = plugin_enabled(selected);
                }

                // update enabled state
                set_center_plugin_enabled(plugin_index, supported);
                if(supported) {
                    update_plugin_content();
                } else {
                    $this.empty();
                }
            });
        });

        // return the jquery selection (or if it was a method call that returned a value - the returned value)
        return returnValue;
    };

})(jQuery);