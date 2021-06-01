var data;
var quality_list;
var hive = new Image();
var bee = new Image();
var home = new Image();
var tandem_bee = new Image();
var follower_bee = new Image();
var bees = [];
var radius;
var hive_locs_x = [];
var hive_locs_y = [];
var num_locs;
var frame;
var time;
var keyframes_x;
var keyframes_y;
var centerHiveH;
var centerHiveV;
var hiveCounts;
var tandems;
var inTandem;
var means;
var vars;
var observations;

function getRandomIntInclusive(min, max) {
  min = Math.ceil(min);
  max = Math.floor(max);
  return Math.floor(Math.random() * (max - min + 1) + min); //The maximum is inclusive and the minimum is inclusive
}

function calcKeyframes()
{
	var last_pos_x = [];
	var last_pos_y = [];
	for (i = 0; i < bees[time].length; i++) {
		if (time == 0 && frame == 0) {
			last_pos_x.push(getRandomIntInclusive(centerHiveH-(hive.width/2), centerHiveH+(hive.width/2)));
			last_pos_y.push(getRandomIntInclusive(centerHiveV-(hive.height/2), centerHiveV+(hive.height/2)));
		}
		else {
			last_pos_x.push(keyframes_x[i][num_frames-1]);
			last_pos_y.push(keyframes_y[i][num_frames-1]);
		}
	}

	keyframes_x = [];
	keyframes_y = [];
	var x1 = [];
	var y1 = [];
	var x2 = [];
	var y2 = [];

	for (i = 0; i < bees[time].length; i++) {
		x1.push(last_pos_x[i]);
		y1.push(last_pos_y[i]);
		x2.push(getRandomIntInclusive(centerHiveH + hive_locs_x[bees[time][i]]-hive.width/2, centerHiveH + hive_locs_x[bees[time][i]]+hive.width/2));
  		y2.push(getRandomIntInclusive(centerHiveV + hive_locs_y[bees[time][i]]-hive.height/2, centerHiveV + hive_locs_y[bees[time][i]]+hive.height/2));
	}

	if (time > 0) {
		var currTandems = tandems[time-1];
		for (i = 0; i < currTandems.length; i++) {
			x2[currTandems[i][1]] = x2[currTandems[i][0]] + 12;
			y2[currTandems[i][1]] = y2[currTandems[i][0]] + 12;
		}
	}

	var nextTandems = tandems[time]
	for (i = 0; i < nextTandems.length; i++) {
		x2[nextTandems[i][1]] = x2[nextTandems[i][0]] + 12;
		y2[nextTandems[i][1]] = y2[nextTandems[i][0]] + 12;
	}

	for (i = 0; i < bees[time].length; i++) {
		var locx = [];
		var locy = [];
		var x_step = (x2[i] - x1[i]) / num_frames;
  		var y_step = (y2[i] - y1[i]) / num_frames;
  		var x = x1[i];
  		var y = y1[i];
  		for (j = 0; j < num_frames + 1; j++) {
  			locx.push(x);
  			x += x_step;
  			locy.push(y);
  			y += y_step;
  		}
  		keyframes_x.push(locx);
  		keyframes_y.push(locy);
	}
}

function configureCanvas(canvas, ctx) {
	canvas.imageSmoothingEnabled = false;

	// get current size of the canvas
	let rect = canvas.getBoundingClientRect();

	// increase the actual size of our canvas
	canvas.width = rect.width * devicePixelRatio;
	canvas.height = rect.height * devicePixelRatio;

	// ensure all drawing operations are scaled
	ctx.scale(devicePixelRatio, devicePixelRatio);

	// scale everything down using CSS
	canvas.style.width = rect.width + 'px';
	canvas.style.height = rect.height + 'px';

	// ctx.globalCompositeOperation = 'destination-over';
  	ctx.clearRect(0, 0, canvas.width, canvas.height);
  	ctx.setTransform(1, 0, 0, 1, 0, 0);
}

function drawBarGraph() {
	var canvas = document.getElementById("BarGraph");
	var ctx = canvas.getContext('2d');
	configureCanvas(canvas, ctx);

	var margin_bottom = 100;
	ctx.font = '24px Mate SC';
	ctx.strokeStyle = 'white';
	ctx.lineWidth = 2;
	ctx.beginPath();
	ctx.moveTo(20, canvas.height-margin_bottom);
	ctx.lineTo(canvas.width-20, canvas.height-margin_bottom);
	ctx.stroke();

	var margin = 50;
	var barWidth = (canvas.width - (margin * (num_locs+1)))/num_locs;
	var maxHeight = canvas.height-margin_bottom-30;

	for (i = 0; i < num_locs; i++) {
		var x = (margin * (i+1)) + (barWidth*i)
		var h = (hiveCounts[time][i]/bees[0].length) * maxHeight;
		ctx.fillStyle = '#3bbca4';
		ctx.fillRect(x, canvas.height-h-margin_bottom, barWidth, h);
		ctx.fillStyle = 'white';
		ctx.fillText('NEST #' + (i+1), x, canvas.height-50);
	}

	var canvas = document.getElementById("ColGraph");
	var ctx = canvas.getContext('2d');
	configureCanvas(canvas, ctx);
	ctx.fillStyle = 'white';

	for (i = 0; i < num_locs; i++) {
		var x = (margin * (i+1)) + (barWidth*i)
		ctx.drawImage(hive, x-5, 20, barWidth+15, barWidth+15);
		ctx.font = '28px Montserrat';
		ctx.fillText((hiveCounts[time][i]/bees[0].length).toFixed(2), x+5, barWidth+7);
		ctx.font = '24px Mate SC';
		ctx.fillText('NEST #' + (i+1), x, canvas.height-55);
	}
}

function drawHiveGraph() {
	var canvas = document.getElementById("HiveGraph");
	var ctx = canvas.getContext('2d');
	configureCanvas(canvas, ctx);

	centerHiveH = canvas.width/2 + 15;
	centerHiveV = canvas.height/2;

  	ctx.translate(centerHiveH, centerHiveV);
  	ctx.drawImage(home, -home.width/2, -home.height/2, home.width, home.height);

  	var angle = 3*Math.PI/2;
  	var angle_step = 2*Math.PI/num_locs;

  	for (i = 0; i < num_locs; i++) {
  		var x = radius * Math.cos(angle);
  		var y = radius * Math.sin(angle);
  		hive_locs_x.push(x);
  		hive_locs_y.push(y);
  		ctx.drawImage(hive, x-hive.width/2, y-hive.height/2, hive.width, hive.height);
  		angle += angle_step;
  	}

  	if (frame == 0 && time == 0) {
		calcKeyframes();
	}

	ctx.fillStyle = 'white';
	ctx.textAlign = 'center'
	for (i = 0; i < num_locs; i++) {
		ctx.font = '24px Mate SC';
		ctx.fillText('NEST #' + (i+1), hive_locs_x[i], hive_locs_y[i] + (hive.height/2) + 40);
		ctx.font = '24px Montserrat';
		ctx.fillText('quality: ' + quality_list[i], hive_locs_x[i], hive_locs_y[i] + (hive.height/2) + 70);
	}

  	for (i = 0; i < bees[time].length; i++)
  	{
  		ctx.setTransform(1, 0, 0, 1, keyframes_x[i][frame], keyframes_y[i][frame]);
  		if (time > 0 && inTandem[time-1][i] == 1)
  			ctx.drawImage(tandem_bee, -bee.width/2, -bee.height/2, bee.width, bee.height);
  		else if (time > 0 && inTandem[time-1][i] == 2)
  			ctx.drawImage(follower_bee, -bee.width/2, -bee.height/2, bee.width, bee.height);
  		else
  			ctx.drawImage(bee, -bee.width/2, -bee.height/2, bee.width, bee.height);
  	}
}

function NormalDensityZx(x, Mean, StdDev) {
  var a = x - Mean;
  return Math.exp(-(a * a) / (2 * StdDev * StdDev)) / (Math.sqrt(2 * Math.PI) * StdDev);
}

function closestIndex(num, arr) {
   let curr = arr[0], diff = Math.abs(num - curr);
   let index = 0;
   for (let val = 0; val < arr.length; val++) {
      let newdiff = Math.abs(num - arr[val]);
      if (newdiff < diff) {
         diff = newdiff;
         curr = arr[val];
         index = val;
      };
   };
   return index;
};

function drawNormalCurves() {
	for (hivenum = 0; hivenum < num_locs; hivenum++) {
		var canvas = document.getElementById("Observation"+(hivenum+1));
		var ctx = canvas.getContext('2d');
		configureCanvas(canvas, ctx);

		var chartData = [];
		var lower = quality_list[hivenum]-3;
		var upper = quality_list[hivenum]+3;
		for (var i = lower; i < upper; i += ((upper-lower)/1000)) {
		  var dp = NormalDensityZx(i, quality_list[hivenum], 1);
		  chartData.push(dp);
		}
 
		var margin_bottom = 70;
		var maxHeight = Math.max(...chartData);
		ctx.font = '24px Mate SC';
		ctx.strokeStyle = 'white';
		ctx.fillStyle = 'white';
		ctx.setTransform(1, 0, 0, 1, 0, 0);
		ctx.fillText('NEST #' + (hivenum+1), (canvas.width/2)-50, canvas.height-30);
		ctx.lineWidth = 2;
		ctx.beginPath();
		ctx.moveTo(0, canvas.height-margin_bottom);
		ctx.lineTo(canvas.width, canvas.height-margin_bottom);
		ctx.stroke();

		for (i = 0; i < chartData.length-1; i++) {
			var x1 = (canvas.width/chartData.length) * i;
			var y1 = ((canvas.height-90)/maxHeight) * chartData[i];
			var x2 = (canvas.width/chartData.length) * (i+1);
			var y2 = ((canvas.height-90)/maxHeight) * chartData[i+1];
			ctx.beginPath();
			ctx.moveTo(x1, canvas.height-y1-margin_bottom);
			ctx.lineTo(x2, canvas.height-y2-margin_bottom);
			ctx.stroke();
		}

		ctx.strokeStyle = '#3bbca4';
		ctx.lineWidth = 1;
		for (i = 0; i < observations[time].length; i++) {
			var loc = bees[time][i];
			if (loc == hivenum) {
				var x = (canvas.width/2)-((canvas.width*(quality_list[hivenum]-observations[time][i]))/6);
				ctx.beginPath();
				ctx.moveTo(x, canvas.height-margin_bottom);
				ctx.lineTo(x, 0);
				ctx.stroke();
			}
		}
	}

	var canvas = document.getElementById("NormalGraph");
	var ctx = canvas.getContext('2d');
	configureCanvas(canvas, ctx);

	var margin_bottom = 70;
	ctx.font = '24px Mate SC';
	ctx.strokeStyle = 'white';
	ctx.fillStyle = 'white';
	ctx.setTransform(1, 0, 0, 1, 0, 0);
	ctx.lineWidth = 2;
	ctx.beginPath();
	ctx.moveTo(0, canvas.height-margin_bottom);
	ctx.lineTo(canvas.width, canvas.height-margin_bottom);
	ctx.stroke();

	var allChartData = [];
	var maxHeight = 0;
	var lowBound = 0;
	var upBound = 0;
	for (hivenum = 0; hivenum < num_locs; hivenum++) {
		var lower = means[bees.length-16][hivenum]-(3*vars[bees.length-16][hivenum]);
		var upper = means[bees.length-16][hivenum]+(3*vars[bees.length-16][hivenum]);
		if (lower < lowBound)
			lowBound = lower;
		if (upper > upBound)
			upBound = upper;
	}

	for (hivenum = 0; hivenum < num_locs; hivenum++) {
		var chartData = [];
		for (var i = lowBound; i < upBound; i += ((upBound-lowBound)/1000)) {
			var dp = NormalDensityZx(i, means[bees.length-1][hivenum], vars[bees.length-1][hivenum]);
			chartData.push(dp);
		}
		var maximum = Math.max(...chartData);
		if (maximum > maxHeight)
			maxHeight = maximum;
	}

	for (hivenum = 0; hivenum < num_locs; hivenum++) {
		var chartData = [];
		for (var i = lowBound; i < upBound; i += ((upBound-lowBound)/1000)) {
			var dp = NormalDensityZx(i, means[time][hivenum], vars[time][hivenum]);
			chartData.push(dp);
		}
		allChartData.push(chartData);
	}

	var colors = ['#1f6155', '#2b8877', '#3bbca4', '#c5ede5', '#64cebb']

	for (hivenum = 0; hivenum < num_locs; hivenum++) {
		for (i = 0; i < allChartData[hivenum].length-1; i++) {
			var x1 = (canvas.width/allChartData[hivenum].length) * i;
			var y1 = ((canvas.height-115)/maxHeight) * allChartData[hivenum][i];
			var x2 = (canvas.width/allChartData[hivenum].length) * (i+1);
			var y2 = ((canvas.height-115)/maxHeight) * allChartData[hivenum][i+1];
			ctx.strokeStyle = colors[hivenum];
			ctx.lineWidth = 4;
			ctx.beginPath();
			ctx.moveTo(x1, canvas.height-y1-margin_bottom);
			ctx.lineTo(x2, canvas.height-y2-margin_bottom);
			ctx.stroke();
			// ctx.strokeStyle = 'white';
			// var texty = canvas.height-(((canvas.height-90)/maxHeight) * allChartData[hivenum][closestIndex(means[time][hivenum], allChartData[hivenum])])-65;
			// ctx.fillText('#'+(hivenum+1), (canvas.width/allChartData[hivenum].length) * closestIndex(means[time][hivenum], allChartData[hivenum])-20, texty);
		}
	}
}

function drawGraphs() {
	drawHiveGraph();
	drawBarGraph();
	drawNormalCurves();

	document.getElementById("TimeValue").innerHTML = time;
	if (time > 0)
		document.getElementById("TandemCount").innerHTML = tandems[time-1].length;
 
 	if (frame < num_frames) {
 		frame++;
 		window.requestAnimationFrame(drawGraphs);
 	}
 	else if (time < bees.length-1 && frame == num_frames) {
 		frame = 0;
 		time++;
 		calcKeyframes(window.requestAnimationFrame);
 		window.requestAnimationFrame(drawGraphs);
 	}
}

function init() {
	hive.src = 'hive.png';
	hive.width = 150;
	hive.height = 150;
	bee.src = 'bee.png';
	bee.width = 10;
	bee.height = 10;
	home.src = 'home.png';
	home.width = 150;
	home.height = 150;
	tandem_bee.src = 'tandem_bee.png';
	follower_bee.src = 'follower_bee.png';
	radius = 300;
	frame = 0;
	time = 0;
	num_frames = 50; //number of frames between each time step
	keyframes_x = [];
	keyframes_y = [];
	data = $.getJSON("c_data.json", function(data){
			hiveCounts = data.sums;
            num_locs = hiveCounts[0].length;
            bees = data.positions;
            quality_list = data.locations;
            tandems = data.tandem;
            inTandem = data.inTandem;
            means = data.means;
            vars = data.vars;
            observations = data.observations;
            window.requestAnimationFrame(drawGraphs);
        }).fail(function(){
            console.log("An error has occurred.");
        });
}

document.addEventListener("DOMContentLoaded", function(event){
	init();
});

