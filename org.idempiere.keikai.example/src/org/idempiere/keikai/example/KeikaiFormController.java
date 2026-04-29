package org.idempiere.keikai.example;

import org.adempiere.webui.panel.ADForm;
import org.adempiere.webui.panel.IFormController;
import org.idempiere.ui.zk.annotation.Form;
import org.zkoss.zk.ui.select.Selectors;

@Form
public class KeikaiFormController implements IFormController {
	private KeikaiForm form;

	public KeikaiFormController() {
		form = new KeikaiForm();
		Selectors.wireEventListeners(form, this);
	}

	@Override
	public ADForm getForm() {
		return form;
	}
}
