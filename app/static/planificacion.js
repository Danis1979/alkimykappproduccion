// Abre el modal de compra con todos los datos cargados
function abrirCompra(ingrediente, cantidadNecesaria = null) {
  // Mostrar el nombre del ingrediente
  document.getElementById("modalIngrediente").value = ingrediente;
  const label = document.getElementById("modalIngredienteLabel");
  if (label) label.textContent = `Compra de: ${ingrediente}`;

  // Mostrar la cantidad necesaria (si viene)
  if (cantidadNecesaria !== null) {
    document.getElementById("modalCantidadNecesaria").value = cantidadNecesaria;
    document.getElementById("modalCantidadComprar").value = "";
  }

  // Setear fecha de hoy
  const hoy = new Date().toISOString().split("T")[0];
  document.getElementById("modalFechaPago").value = hoy;

  // Mostrar el modal
  const modal = new bootstrap.Modal(document.getElementById("modalCompraIngrediente"));
  modal.show();
}

// Guardar proveedor
document.getElementById("formNuevoProveedor").addEventListener("submit", async function (e) {
  e.preventDefault();

  const nombre = document.getElementById("nuevoProveedorNombre").value.trim();
  if (!nombre) {
    alert("Debe ingresar un nombre para el proveedor");
    return;
  }

  const response = await fetch("/agregar_proveedor", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nombre })
  });

  const data = await response.json();

  if (response.ok && data.success) {
    alert(data.message || "Proveedor guardado con éxito");

    const proveedorSelect = document.getElementById("modalProveedor");
    if (![...proveedorSelect.options].some(opt => opt.value === data.nombre)) {
      const nuevoOption = document.createElement("option");
      nuevoOption.value = data.nombre;
      nuevoOption.textContent = data.nombre;
      proveedorSelect.appendChild(nuevoOption);
    }
    proveedorSelect.value = data.nombre;

    document.getElementById("formNuevoProveedor").reset();
    const modalElement = document.getElementById("modalAgregarProveedor");
    const modal = bootstrap.Modal.getInstance(modalElement) || new bootstrap.Modal(modalElement);
    modal.hide();
  } else {
    alert(data.message || "Error al guardar el proveedor");
  }
});

// Guardar compra de ingrediente
document.getElementById("formCompraIngrediente").addEventListener("submit", async function (e) {
  e.preventDefault();

  const ingrediente = document.getElementById("modalIngrediente").value;
  const cantidad = document.getElementById("modalCantidadComprar").value;
  const proveedor = document.getElementById("modalProveedor").value;
  const forma_pago = document.getElementById("modalFormaPago").value;
  const fecha_pago = document.getElementById("modalFechaPago").value;

  const response = await fetch("/guardar_compra", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ingrediente, cantidad, proveedor, forma_pago, fecha_pago })
  });

  const data = await response.json();

  if (response.ok && data.success) {
    alert(data.message);
    const modal = bootstrap.Modal.getInstance(document.getElementById("modalCompraIngrediente"));
    modal.hide();
    document.getElementById("formCompraIngrediente").reset();
    // Podrías también actualizar visualmente lo pendiente, si querés
  } else {
    alert(data.message || "Error al registrar la compra");
  }
});