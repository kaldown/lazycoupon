const { openBrowser, goto, click, textBox, into, write, closeBrowser } = require('taiko');
const redis = require("redis");


const taskChannel = 'TASK_CHANNEL';

const sub = redis.createClient();
const pub = redis.createClient();

sub.subscribe(taskChannel);


async function pushEvent(funcName, obj) {
	message = {};
	message['func_name'] = funcName;
	message['arguments'] = obj;

	message = JSON.stringify(message);
	pub.publish(taskChannel, message);
}


async function done() {
	sub.unsubscribe();
        sub.quit();
        pub.quit();
	await closeBrowser();
}


async function setPhone(obj) {
	phone = obj['provider_phone']
	console.log('setting phone: ' + phone)

	await write(phone, into(textBox({placeholder: "номер телефона"})));
	await click("Получить код");

	await pushEvent('get_code', obj);
}


async function setCode(obj) {
	code = obj['provider_code']
	console.log('setting code: ' + code)

	await write(code, into(textBox({placeholder: "Код из СМС"})));

	await pushEvent('chose_seller', obj);
}


async function fillField(text, label) {
	await clear(textBox({id: label}));
	await write(text, into(textBox({id: label})));
}


async function choseSeller(obj) {
	console.log('chosing seller: ' + 'Forneria')  // by default ofc

	await write("Сокольническая площадь, 4с1", into(textBox({placeholder: "Укажите адрес доставки..."})));
        await click("Показать рестораны");
	// not neccessary
        //await click("Пицца");
	await write("Forneria", into(textBox({placeholder: "Название, кухня или блюдо"})));
        await click("Forneria");

	// TODO: add randomizer
        await click("Пицца Грибная");
	// TODO: only when closed
	//await click(button("Оформить предзаказ"));
        await click("Пицца Мясная");

	await click("Оформить заказ");

	await fillField("Charli Chaplin", "id_3"); 			  // fio
	await fillField("charli@chap.lin", "id_4"); 		  	  // email
	await fillField("36", "id_6"); 					  // apt
	await fillField("36ZBS", "id_7"); 				  // doordash
	await fillField("2", "id_8"); 					  // porch
	await fillField("3", "id_9"); 				       	  // level
	await fillField("люблю кушать пиццу на дровах", "id_10");	  // comment
	await fillField("START", "id_11");				  // coupon
	await click(button("Применить")); 				  // accept coupon
	await click($("//div[contains(@class, 'UICounter_decrement')]")); // clean trash

	await click(button("Перейти к оплате"));
}


async function setCoupon(obj) {
	console.log('coming soon')
}


async function dispatch(channel, message) {
	console.log('[front] MSG:' + message)
	obj = JSON.parse(message)

	if (Object.keys(obj).length) {
		funcName = obj['func_name']
		if (funcName in FUNCTIONS) {
			func = FUNCTIONS[funcName]
			try {
				func(obj['arguments'])
			} catch (err) {
				console.error('[front] error' + err)
			}
		}
	}
}


FUNCTIONS = {}
FUNCTIONS['set_phone'] = setPhone
FUNCTIONS['set_code'] = setCode
FUNCTIONS['chose_seller'] = choseSeller
FUNCTIONS['set_coupon'] = setCoupon
FUNCTIONS['quit'] = done


function subscribe() {
	return new Promise(resolve => {
		sub.on('message', function (channel, message) {
			resolve(dispatch(channel, message));
		});
	});
}


(async () => {
    try {
        await openBrowser();
        await goto("http://eda.yandex");
        await click("Войти");
	await subscribe();
    } catch (error) {
        console.error('[front] error' + err);
	await done();
    }
})();
