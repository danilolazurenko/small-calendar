
var today = new Date();
var cur_day = today.getDate();
var cur_mo = today.getMonth()+1;
var cur_year = today.getFullYear();

function get_num_days(month){
if (month == 2 && (cur_year % 4) ==0){var m_days = 29;}
else if (month==2){var m_days=28;}
else if ((month%2 == 0) && (month<7)){var m_days=30;}
else if ((month%2 != 0) && (month<=7)){var m_days=31;}
else if ((month%2 == 0) && (month>=8)){var m_days=31;}
else if ((month%2 != 0) && (month>8)){var m_days=30;}
return m_days
}

var daysAndMonth={};
for(i=1;i<13;i++){
daysAndMonth[i] = [];}
for(i=1;i<13;i++){
for(j=1;j<=get_num_days(i);j++){
daysAndMonth[i] = daysAndMonth[i].concat([j]);
}
}

function changeDaysInMonth() {
    var monList = document.getElementById("mon");
    var dayList = document.getElementById("daynum");
    var selMon = monList.options[monList.selectedIndex].value;
    while (dayList.options.length) {
        dayList.remove(0);
    }
    var months = daysAndMonth[selMon];
    if (months) {
        for (var i = 0; i < months.length; i++) {
            var mon = new Option(months[i],i);
            dayList.options.add(mon);
        }
    }
} 
