document.addEventListener('DOMContentLoaded', (event) => {
    const ctx = document.getElementById('fillLevelChart').getContext('2d');
  
    const data = {
      labels: ['January', 'February', 'March', 'April', 'May', 'June', 'July'],
      datasets: [{
        label: 'Fill Level',
        data: [0, 43, 50, 81, 56, 55, 40],
        fill: false,
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.4, // This value makes the line wavy
        additionalInfo: ['07/01', '24/02', '09/03', '18/04', '11/05', '12/06', '12/07']
      }]
    };
  
    const config = {
      type: 'line',
      data: data,
      options: {
        scales: {
          x: {
            beginAtZero: true,
            grid: {
              display: false // This removes the vertical lines
            }
          },
          y: {
            beginAtZero: true,
            grid: {
              display: true // This keeps the horizontal lines
            }
          }
        },
        plugins: {
            tooltip: {
              backgroundColor: 'rgba(87, 186, 152, 1)', // Background color of the tooltip
              borderColor: 'rgba(0, 0, 0, 0.2)', // Border color of the tooltip
              borderWidth: 1, // Border width of the tooltip
              borderRadius: 4, // Border radius of the tooltip
              padding: 10, // Padding of the tooltip content
              displayColors: false, // Whether to display color boxes in the tooltip
              shadowOffsetX: 2, // Horizontal shadow offset
              shadowOffsetY: 2, // Vertical shadow offset
              shadowBlur: 5, // Shadow blur radius
              shadowColor: 'rgba(0, 0, 0, 0.3)', // Shadow color
              callbacks: {
                label: function(context) {
                  const index = context.dataIndex;
                  const additionalInfo = context.dataset.additionalInfo[index];
                  const value = context.raw;
                  return `Value: ${value}, Date: ${additionalInfo}`;
                }
              },
              bodyFont: {
                size: 14, // Font size of the tooltip body
                weight: 'normal', // Font weight of the tooltip body
                color: 'rgba(256, 256, 256, 0.3)' // Font color of the tooltip body
              }
            }
          }
        }
      };
    const fillLevelChart = new Chart(ctx, config);
  });


  $(function(){
    var $ppc = $('.progress-pie-chart'),
      percent = parseInt($ppc.data('percent')),
      deg = 360*percent/100;
    if (percent > 50) {
      $ppc.addClass('gt-50');
    }
    $('.ppc-progress-fill').css('transform','rotate('+ deg +'deg)');
    $('.ppc-percents span').html(percent+'%');
  });
  