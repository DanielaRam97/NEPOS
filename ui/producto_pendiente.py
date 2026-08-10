from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from services.producto_pendiente_service import (
    ErrorProductoPendiente,
    crear_producto_provisorio,
)


class DialogoProductoPendiente(QDialog):
    def __init__(self, codigo, usuario, parent=None):
        super().__init__(parent)
        self.usuario = usuario
        self.producto_creado = None
        self.setWindowTitle("Producto no registrado")
        self.setModal(True)
        self.setFixedWidth(470)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Alta provisoria</h2>"))
        ayuda = QLabel(
            "El producto podrá venderse ahora, pero quedará marcado como "
            "PENDIENTE DE REVISIÓN hasta que ADMIN complete y apruebe sus datos."
        )
        ayuda.setWordWrap(True)
        layout.addWidget(ayuda)

        form = QFormLayout()
        self.campo_codigo = QLineEdit(codigo)
        self.campo_descripcion = QLineEdit()
        self.campo_precio = QLineEdit()
        self.campo_precio.setPlaceholderText("Acepta punto o coma decimal")
        self.check_pesable = QCheckBox("Producto pesable")
        form.addRow("Código:", self.campo_codigo)
        form.addRow("Descripción:", self.campo_descripcion)
        form.addRow("Precio provisorio:", self.campo_precio)
        form.addRow("", self.check_pesable)
        layout.addLayout(form)

        boton = QPushButton("Guardar y agregar a la venta")
        boton.setStyleSheet(
            "background: #13aa52; color: white; font-weight: bold; padding: 10px;"
        )
        boton.clicked.connect(self.guardar)
        layout.addWidget(boton)

    @staticmethod
    def _numero(texto):
        valor = str(texto or "").strip().replace(" ", "").replace("$", "")
        if not valor:
            raise ValueError
        if "," in valor and "." in valor:
            if valor.rfind(",") > valor.rfind("."):
                valor = valor.replace(".", "").replace(",", ".")
            else:
                valor = valor.replace(",", "")
        else:
            valor = valor.replace(",", ".")
        return float(valor)

    def guardar(self):
        try:
            precio = self._numero(self.campo_precio.text())
            self.producto_creado = crear_producto_provisorio(
                codigo=self.campo_codigo.text(),
                descripcion=self.campo_descripcion.text(),
                precio_provisorio=precio,
                pesable=self.check_pesable.isChecked(),
                usuario_id=self.usuario.id,
            )
        except ValueError:
            QMessageBox.warning(
                self,
                "Precio inválido",
                "Ingresá un precio numérico.",
            )
            return
        except ErrorProductoPendiente as error:
            QMessageBox.warning(
                self,
                "No se pudo crear",
                str(error),
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                "Error",
                str(error),
            )
            return

        QMessageBox.information(
            self,
            "Producto provisorio creado",
            "Se agregó a la venta y quedó pendiente de revisión por ADMIN.",
        )
        self.accept()
