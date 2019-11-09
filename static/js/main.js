// List-up the top20 players named to the dropdown menu
d3.json('static/db/players.json').then(dropDownMenuOrganizer);

var shotChart = d3.select('.shot-chart');

svgWidth = 900;
svgHeight = 700;

var margin = {
    top: 40.19,
    right: 30.059,
    bottom: 30,
    left: 30.059
};

const svg = shotChart.append('svg')
    .attr('preserveAspectRatio', 'xMinYMin meet')
    .attr('xmlns', 'http://www.w3.org/2000/svg')
    .attr('viewBox', `-50 0 ${svgWidth} ${svgHeight}`);


// Get the dimensions for shot zone
const courtWidth = 470.364 + margin.right;
var halfCourtHeight = 470;

const groups = {
    court: svg.append('g').attr('class', 'court'),
    hoop: svg.append('g').attr('class', 'hoop'),
    shotGroup: svg.append('g')
        .attr('class', 'shots')
        .attr('width', courtWidth) // courtWidth is a global variable
        .attr('height', halfCourtHeight) // halfCourtHeight is also in global scope
};

// scaling for shot x
var xScaler = d3.scaleLinear()
    .domain([-246, 245])
    .range([0, courtWidth]);

// scaling for shot y
var yScaler = d3.scaleLinear()
    .domain([-8, 430])
    .range([margin.top, halfCourtHeight]);


// Draw a court
drawCourt();
// Listen for user-inputted shotchart 
userInputListener();

// Draw shots when selecting a player on the dropdown menu
var playerDropDown = $('.selectpicker')
playerDropDown.change(function() {
    let playerId = playerDropDown.val();

    d3.json(`/shotchart/${playerId}`).then((response) => {
        const randonmizedShots = knuthShuffle(response, 10000);
        drawShots(randonmizedShots, courtWidth, halfCourtHeight, xScaler, yScaler);
    });
    getPlayerImage(playerId);
});


function userInputListener() {

    var userShots = [];
    const userClickableArea = svg.append('g')
        .attr('class', 'userClickableArea')

    userClickableArea.append('rect')
        .attr('x', '0')
        .attr('width', `${(470.364 + 30.059)}`)
        .attr('height', '470')
        .on("click", mouseClick);

    function mouseClick(d) {
        const [x, y] = d3.mouse(this);
        const [shotX, shotY] = [
            Math.floor(xScaler.invert(x)),
            Math.floor(yScaler.invert(y))
        ]

        userShots.push({ x: shotX, y: shotY })

        console.log(`X=${x}, Y=${y}`);
        console.log(`Shot X=${shotX}, Shot Y=${shotY}`);

        userClickableArea.append('circle')
            .attr('class', 'userShot')
            .attr('cx', x)
            .attr('cy', y)
            .attr('r', '5');
    }

    d3.select('#button1').on('click', function() {
        console.log(userShots);
    });
}

function getPlayerImage(playerId) {

    const image = d3.select("#player-image")
    console.log(image);
    image.attr('src', `http://stats.nba.com/media/players/230x185/${playerId}.png`)
        .attr('alt', playerId);
}

function drawShots(shots) {
    // draw shots

    // create a svg group for shot zone based on the dimensions above
    const shotGroup = groups.shotGroup;
    shotGroup.selectAll('circle').remove();

    // create axes
    // const yAxis = d3.axisLeft(yScaler);
    // const xAxis = d3.axisBottom(xScaler);
    // shotGroup.append('g')
    //     .call(yAxis);
    // shotGroup.append('g')
    //     .attr('transform', `translate(0, ${halfCourtHeight})`)
    //     .call(xAxis);

    shotGroup.selectAll('circle')
        .data(shots)
        .enter()
        .append('circle')
        .attr('fill', d => {
            if (d.EVENT_TYPE === "Made Shot") return 'green'
            else return 'red'
        })
        .attr('cx', d => xScaler(d.LOC_X))
        .attr('cy', d => yScaler(d.LOC_Y))
        .attr('r', '5');
}


function drawCourt() {
    const courtGroup = groups.court;
    const hoopGroup = groups.hoop;

    // Draw a polyline for the court
    courtGroup.append('polyline')
        .attr('points', '470.364,137.064 470.364,0 30.059,0 30.059,137.064');

    // rects
    courtGroup.append('rect')
        .attr('x', '170.196')
        .attr('width', '160.033')
        .attr('height', '189.945');

    courtGroup.append('rect')
        .attr('x', '0')
        .attr('width', `${(470.364 + 30.059)}`)
        .attr('height', '470');

    // paths
    courtGroup.append('path')
        .attr('d', 'M190.518,189.945 c0,32.943,26.726,59.65,59.694,59.65c32.97,0,59.695-26.707,59.695-59.65');

    courtGroup.append('path')
        .attr('d', 'M210.729,52.773 c2.745,21.792,22.653,37.229,44.459,34.486c18.033-2.269,32.236-16.464,34.509-34.486');

    courtGroup.append('path')
        // .attr('stroke-dasharray', '13.33,11.67')
        .attr('d', 'M309.907,189.945c0-32.943-26.726-59.649-59.695-59.649c-32.969,0-59.694,26.706-59.694,59.649');

    courtGroup.append('path')
        .attr('d', 'M30.203,137.058 c49.417,121.198,187.98,179.485,309.489,130.194c59.332-24.068,106.401-71.017,130.529-130.194');

    courtGroup.append('path')
        .attr('d', 'M309.907,470 c0-32.945-26.726-59.65-59.695-59.65c-32.969,0-59.694,26.705-59.694,59.65');

    // lines
    courtGroup.append('line')
        .attr('x1', `${170.196 - ((190.094 - 170.196) * 1.5)}`)
        .attr('y1', '0')
        .attr('x2', `${170.196 - ((190.094 - 170.196) * 1.5)}`)
        .attr('y2', '10');

    courtGroup.append('line')
        .attr('x1', `${(170.196 + 160.033) + (((170.196 + 160.033) - 310.331) * 1.5)}`)
        .attr('y1', '0')
        .attr('x2', `${(170.196 + 160.033) + (((170.196 + 160.033) - 310.331) * 1.5)}`)
        .attr('y2', '10');

    courtGroup.append('line')
        .attr('x1', '30.059')
        .attr('y1', '137.064')
        .attr('x2', '0')
        .attr('y2', '137.064');

    courtGroup.append('line')
        .attr('x1', '470.364')
        .attr('y1', '137.064')
        .attr('x2', `${470.364 + 30.059}`)
        .attr('y2', '137.064');

    courtGroup.append('line')
        .attr('x1', '30.059')
        .attr('y1', `${137.064 * 2}`)
        .attr('x2', '0')
        .attr('y2', `${137.064 * 2}`);

    courtGroup.append('line')
        .attr('x1', '470.364')
        .attr('y1', `${137.064 * 2}`)
        .attr('x2', `${470.364 + 30.059}`)
        .attr('y2', `${137.064 * 2}`);

    courtGroup.append('line')
        .attr('x1', '310.331')
        .attr('y1', '189.945')
        .attr('x2', '310.331')
        .attr('y2', '0');

    courtGroup.append('line')
        .attr('x1', '190.094')
        .attr('y1', '189.945')
        .attr('x2', '190.094')
        .attr('y2', '0');

    courtGroup.append('line')
        .attr('x1', '330.229')
        .attr('y1', '0')
        .attr('x2', '340.391')
        .attr('y2', '0');

    courtGroup.append('line')
        .attr('x1', '340.391')
        .attr('y1', '145.95')
        .attr('x2', '330.229')
        .attr('y2', '145.95');

    courtGroup.append('line')
        .attr('x1', '340.391')
        .attr('y1', '114.223')
        .attr('x2', '330.229')
        .attr('y2', '114.223');

    courtGroup.append('line')
        .attr('x1', '340.391')
        .attr('y1', '82.495')
        .attr('x2', '330.229')
        .attr('y2', '82.495');

    courtGroup.append('line')
        .attr('x1', '340.391')
        .attr('y1', '71.071')
        .attr('x2', '330.229')
        .attr('y2', '71.071');

    courtGroup.append('line')
        .attr('x1', '160.032')
        .attr('y1', '145.95')
        .attr('x2', '170.196')
        .attr('y2', '145.95');

    courtGroup.append('line')
        .attr('x1', '160.032')
        .attr('y1', '114.223')
        .attr('x2', '170.196')
        .attr('y2', '114.223');

    courtGroup.append('line')
        .attr('x1', '160.032')
        .attr('y1', '82.495')
        .attr('x2', '170.196')
        .attr('y2', '82.495');

    courtGroup.append('line')
        .attr('x1', '160.032')
        .attr('y1', '71.071')
        .attr('x2', '170.196')
        .attr('y2', '71.071');

    // Draw a hoop in the court
    hoopGroup.append('line')
        .attr('class', 'backboard')
        .style('stroke-width', '5.0')
        .attr('x1', '280.271')
        .attr('y1', '40.19')
        .attr('x2', '220.151')
        .attr('y2', '40.19');

    hoopGroup.append('path')
        .attr('class', 'rim')
        .attr('d', 'M250.212,54.993 c3.977,0,7.197-3.215,7.197-7.188c0-3.977-3.221-7.192-7.197-7.192c-3.976,0-7.197,3.216-7.197,7.192 C243.015,51.778,246.236,54.993,250.212,54.993z');
}


function knuthShuffle(arr, elements) {
    var rand, temp, i;

    for (i = arr.length - 1; i > 0; i -= 1) {
        rand = Math.floor((i + 1) * Math.random()); //get random between zero and i (inclusive)
        temp = arr[rand]; //swap i and the zero-indexed number
        arr[rand] = arr[i];
        arr[i] = temp;
    }
    return arr.slice(0, elements);
}


function dropDownMenuOrganizer(jsonData) {
    // Assign items to dropdown selections
    // Sort them and prevent duplicates
    const options = [];

    jsonData.sort((a, b) => {
        if (a.PLAYER_NAME > b.PLAYER_NAME) {
            return 1
        } else {
            return -1
        }
    }).forEach((player, index) => {
        const option = `<option value=${player.PLAYER_ID}> ${player.PLAYER_NAME} </option>`;
        options.push(option)
    });

    d3.select(".selectpicker").html(options)
    $('.selectpicker').selectpicker('refresh');
}