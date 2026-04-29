package org.idempiere.keikai.example;

import java.io.ByteArrayOutputStream;
import java.io.OutputStream;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

import org.adempiere.webui.panel.CustomForm;
import org.zkoss.util.media.AMedia;
import org.zkoss.zk.ui.Component;
import org.zkoss.zk.ui.Executions;
import org.zkoss.zk.ui.select.Selectors;
import org.zkoss.zul.Filedownload;

public class KeikaiForm extends CustomForm {
	private static final long serialVersionUID = 20260427L;
	private static final DateTimeFormatter TS_FORMAT = DateTimeFormatter.ofPattern("yyyyMMdd-HHmmss");

	public KeikaiForm() {
		Component form = null;
		ClassLoader cl = Thread.currentThread().getContextClassLoader();
		try {
			// CRITICAL: DO NOT REMOVE THIS BLOCK.
			// ZK resolves "~./" resources through the thread context classloader.
			// Without this swap, iDempiere/ZK may look in org.adempiere.ui.zk
			// instead of this plugin bundle and fail to load the ZUL.
			Thread.currentThread().setContextClassLoader(getClass().getClassLoader());
			form = Executions.createComponents("~./keikai-form.zul", this, null);
			registerExampleActions(form.getFellow("spreadsheet"));
		} finally {
			Thread.currentThread().setContextClassLoader(cl);
		}

		Selectors.wireComponents(form, this, false);
	}

	private void registerExampleActions(Component spreadsheet) {
		try {
			ClassLoader keikaiCl = spreadsheet.getClass().getClassLoader();
			Object actionManager = spreadsheet.getClass().getMethod("getUserActionManager").invoke(spreadsheet);
			Class<?> handlerType = Class.forName("io.keikai.ui.UserActionHandler", true, keikaiCl);
			Method registerHandler = actionManager.getClass().getMethod("registerHandler", String.class, String.class,
					handlerType);
			String category = getAuxActionCategory(keikaiCl);

			registerHandler.invoke(actionManager, category, getAuxAction(keikaiCl, "SAVE_BOOK"),
					newUserActionHandler(handlerType, new SaveBookAction(keikaiCl)));
			registerHandler.invoke(actionManager, category, getAuxAction(keikaiCl, "EXPORT_PDF"),
					newUserActionHandler(handlerType, new ExportPdfAction(keikaiCl)));
		} catch (Exception e) {
			throw new IllegalStateException("Unable to register Keikai example actions", e);
		}
	}

	private Object newUserActionHandler(Class<?> handlerType, ExampleAction action) {
		InvocationHandler handler = (proxy, method, args) -> {
			String name = method.getName();
			if ("isEnabled".equals(name)) {
				return args != null && args.length >= 2 && args[0] != null && args[1] != null;
			}
			if ("process".equals(name)) {
				action.process(args[0]);
				return Boolean.TRUE;
			}
			if ("toString".equals(name)) {
				return action.getClass().getSimpleName();
			}
			if ("hashCode".equals(name)) {
				return System.identityHashCode(proxy);
			}
			if ("equals".equals(name)) {
				return proxy == args[0];
			}
			return null;
		};
		return Proxy.newProxyInstance(handlerType.getClassLoader(), new Class<?>[] { handlerType }, handler);
	}

	private String getAuxActionCategory(ClassLoader keikaiCl) throws Exception {
		Class<?> categoryType = Class.forName("io.keikai.ui.impl.DefaultUserActionManagerCtrl$Category", true,
				keikaiCl);
		Object auxAction = Enum.valueOf(categoryType.asSubclass(Enum.class), "AUXACTION");
		return (String) categoryType.getMethod("getName").invoke(auxAction);
	}

	private String getAuxAction(ClassLoader keikaiCl, String name) throws Exception {
		Class<?> auxActionType = Class.forName("io.keikai.ui.AuxAction", true, keikaiCl);
		Object action = Enum.valueOf(auxActionType.asSubclass(Enum.class), name);
		return (String) auxActionType.getMethod("getAction").invoke(action);
	}

	private static Object invoke(Object target, String methodName, Class<?>[] parameterTypes, Object... args)
			throws Exception {
		Method method = target.getClass().getMethod(methodName, parameterTypes);
		return method.invoke(target, args);
	}

	private static Object invoke(Object target, String methodName) throws Exception {
		return invoke(target, methodName, new Class<?>[0]);
	}

	private interface ExampleAction {
		void process(Object context) throws Exception;
	}

	private static final class SaveBookAction implements ExampleAction {
		private final ClassLoader keikaiCl;

		private SaveBookAction(ClassLoader keikaiCl) {
			this.keikaiCl = keikaiCl;
		}

		@Override
		public void process(Object context) throws Exception {
			Object book = invoke(context, "getBook");
			String bookName = normalizeBookName((String) invoke(book, "getBookName"), "xlsx");
			ByteArrayOutputStream out = new ByteArrayOutputStream();
			exportWorkbook(book, bookName, out);
			Filedownload.save(new AMedia(bookName, "xlsx",
					"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", out.toByteArray()));
		}

		private void exportWorkbook(Object book, String bookName, OutputStream out) throws Exception {
			exportBook(keikaiCl, book, bookName.endsWith(".xls") ? "xls" : "xlsx", out);
		}
	}

	private static final class ExportPdfAction implements ExampleAction {
		private final ClassLoader keikaiCl;

		private ExportPdfAction(ClassLoader keikaiCl) {
			this.keikaiCl = keikaiCl;
		}

		@Override
		public void process(Object context) throws Exception {
			Object book = invoke(context, "getBook");
			String bookName = normalizeBookName((String) invoke(book, "getBookName"), "pdf");
			ByteArrayOutputStream out = new ByteArrayOutputStream();
			exportBook(keikaiCl, book, "pdf", out);
			Filedownload.save(new AMedia(bookName, "pdf", "application/pdf", out.toByteArray()));
		}
	}

	private static void exportBook(ClassLoader keikaiCl, Object book, String format, OutputStream out)
			throws Exception {
		Class<?> exportersType = Class.forName("io.keikai.api.Exporters", true, keikaiCl);
		Object exporter = exportersType.getMethod("getExporter", String.class).invoke(null, format);
		Class<?> bookType = Class.forName("io.keikai.api.model.Book", true, keikaiCl);
		exporter.getClass().getMethod("export", bookType, OutputStream.class).invoke(exporter, book, out);
	}

	private static String normalizeBookName(String bookName, String extension) {
		String base = bookName != null && !bookName.isBlank() ? bookName : "Keikai-Example";
		int dot = base.lastIndexOf('.');
		if (dot > 0) {
			base = base.substring(0, dot);
		}
		if ("Book".equals(base) || "blank".equalsIgnoreCase(base)) {
			base = "Keikai-Example-" + TS_FORMAT.format(LocalDateTime.now());
		}
		return base + "." + extension;
	}
}
