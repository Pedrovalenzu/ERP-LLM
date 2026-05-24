document.addEventListener("DOMContentLoaded", function() {
    
    const canvas = document.getElementById('graficoStock');
    
    //Si canva existe
    if (canvas) {
        const etiquetas = JSON.parse(canvas.getAttribute('data-labels'));//convierte el texto en listas otra vez
        const cantidades = JSON.parse(canvas.getAttribute('data-valores'));

        const ctx = canvas.getContext('2d');

        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: etiquetas,
                datasets: [{
                    label: 'Unidades',
                    data: cantidades,
                    backgroundColor: 'rgb(255, 163, 58)',
                    borderColor: 'rgb(219, 106, 0)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }


    const canvasprov = document.getElementById('graficoProv');
    
    //Si canva existe
    if (canvasprov) {
        const etiquetas = JSON.parse(canvasprov.getAttribute('data-labels'));//convierte el texto en listas otra vez
        const cantidades = JSON.parse(canvasprov.getAttribute('data-valores'));

        const ctxProv = canvasprov.getContext('2d');

        
        new Chart(ctxProv, {
        type: 'pie',
        data: {
            labels: etiquetas,
            datasets: [{
                label: 'Total Pedidos',
                data: cantidades,
                backgroundColor: [
                    'rgba(255, 163, 58, 0.6)',  
                    'rgba(54, 162, 235, 0.6)',  
                    'rgba(75, 192, 192, 0.6)',  
                    'rgba(153, 102, 255, 0.6)', 
                    'rgba(255, 99, 132, 0.6)'   
                ],
                borderColor: [
                    'rgba(255, 163, 58, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)',
                    'rgba(255, 99, 132, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false 
        }
        });
    }
});