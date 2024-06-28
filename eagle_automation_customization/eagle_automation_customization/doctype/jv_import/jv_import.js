// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("JV Import", {
	refresh(frm) {
        frm.add_custom_button(__('Start Import'), function() {
            frm.call("import_data").then(r => {
                if(!r.exc){
                    frappe.msgprint("Import Initiated successfully");
                    setTimeout(() => {
                        window.location.reload();
                    }, 2000);
                }
            })
        });

        frm.add_custom_button(__("Go To Journal Entry"), () =>
				frappe.set_route("list", "Journal Entry")
			);
        cur_frm.get_field('preview').$wrapper.html("")

        frm.call('preview_error_log').then(r => {
            if (r.message && ["Failed", "Partially Imported"].includes(frm.doc.status)) {
                let msg = "<h3>Error While Importing JV</h3>"
                cur_frm.get_field('error_preview').$wrapper.html(msg + r.message)
            }else{
                cur_frm.get_field('error_preview').$wrapper.html("")
            }

            var coll = document.getElementsByClassName("collapsible_c");
            for (var i = 0; i < coll.length; i++) {
                coll[i].addEventListener("click", function() {
                    this.classList.toggle("active_c");
                    var content = this.nextElementSibling;

                    if (content.style.display === "block") {
                        content.style.display = "none";
                    } else {
                        content.style.display = "block";
                    }
                });
            }
        })
    },
    show_preview: function(frm) {
        frm.call("preview_data").then(r => {
            cur_frm.get_field('preview').$wrapper.html(r.message)
        })
    }
});
