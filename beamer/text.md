### Титульный слайд

Здравствуйте, меня зовут Польшаков Дмитрий. Тема моей работы:
Исследование возможности добавления палитры команд в произвольные приложения
c использованием фреймворка Qt

### Постановка задачи

Чтобы выполнить это нужно было проанализировать возможности добавления функции в
существующие приложения. Затем разработать программу управления, которая бы
запускала другие приложения и отображала палитру команд. Отдельно разработать
модуль, который бы собирал информацию об элементах интерфейса и активировал их
по команде.

### Палитра команд

Что такое палитра команд?
Это специальное окно в интерфейсе приложения, где отображаются все доступные
функции. Иногда рядом с описанием функции отображается горячая клавиша для
её активации.

Впервые палитра команд была добавлена в текстовый редактор Sublime
text в июле 2011 года. Затем их начали добавлять в другие приложения: visual
studio code, jupyter noteboot и т.д.

### Plotinus

Но это были лишь единичные случаи. В апреле 2017 года появилась первая версия
приложения Plotinus. Это дополнительный модуль для приложений, использующих GTK.
Его можно специальным образом загрузить при запуске приложения и он
автоматически добавит палитру команд.

Однако, как было сказано, это работает только для фреймворка GTK. Однако
насколько этого достаточно?

#### Фреймворк Qt

В операционной системе Linux графические приложения делятся на две примерно
равные группы относительно используемой графической библиотеки. Это GTK и Qt.
GTK написан на языке Си, а Qt на языке C++. Оба расширяют возможности языка для
разработки прикладных программ. В частности графических приложений

#### Добавление функциональности

Итак. Как мы можем добавить функциональность в приложение?

Во-первых, разработчик может подключить библиотеку и написать соответствующий
код для работы с неё. Недостатком такого подхода, очевидно является то, что
такое добавление может сделать только сам разработчик программы.

Во-вторых, это добавление функционала в собранную программу. Самым
распространенным примером такого подхода являются плагины. Если разработчик
исходной программы написал код, который работает с плагинами, то этот подход
позволяет другим людям расширять функциональность основного приложения.

Но далеко не все программы поддерживают возможность подключения плагинов.
Тогда был выбран единственный доступный вариант: внедрение дополнительной логики
при взаимодействии подсистем. Для того, чтобы понять, что имеется в виду,
рассмотрим цепочку взаимодействия пользователя с интерфейсом, чтобы понять, где
именно можно произвести внедрение.

#### Взаимодействие элементов

На слайде схемотично представлен механизм, как пользователь производит действия.
Он кликает мышкой или нажимает клавишу, информация об этом обрабатывается
графической системой X11. Затем графическая система передает информацию
активному приложению. В приложении первоначальной обработкой событий занимается
графическая библиотека. Когда обязательные действия были выполнены, приложение
может произвести дополнительную обработку.

Изменить способ взаимодействия с системой мы не можем, т.к. графическая оболочка
очень плотно интегрирована в операционную систему. Остаются два варианта: между
X11 и Qt или между Qt и приложением.

Первой идеей было запрашивать у графической подсистему информацию об
отрисованных элементов. Однако оказалось, что Qt занимается отрисовкой объектов
самостоятельно и передает информацию уже в виде изображения. Как следствие,
сторонний наблюдатель не может узнавать, какие элементы в прилоежнии есть.

#### Внедрение библиотеки

Остался один вариант: внедриться между приложением и графической библиотекой
и сохранять список всех создаваемых объектов, а затем вызывать функции, которые
бы приводили к их активации.

Каким образом это можно сделать?

#### Механизм подмены функций

Из-за того, что графическая библиотека достаточно тяжеловестна и используется
многими приложениями, они связывается с приложением динамически. Это значит, что
приложение при запуске попросить загрузчик поместить библиотеку в память и
выдать адреса некоторых её функций.

Загрузчик, используемый в Linux (ld) позволяет загрузить дополнительные
библиотеки раньше всех. Это приводит к тому, что приложение получит адреса не
оригинальных функций, а функций из библиотеки.

Функция из этой самой внедренной библиотеки в свою очередь выполнит свою работу,
запросит у загрузчика реальный адрес функции и вызовет её, что позволит
сохранить стандартное поведение.

#### Искажение имен

Однако тут мы сталкиваемся с новой проблемой. Изначально библиотеки в Linux были
разработаны для работы с языком Си и поэтому не реализуют такие понятия как
классы, пространства имен и перегрузки. Для сохранения всей этой информации,
компиляторы специальным образом формируют имена функций и методов. В случае
компилятора gcc используется стандарт Itanium. На слайде вы можете видеть
пример, как преобразуется имя конструктора и имя метода в идентификатор, который
будет записан в таблицу вызовов библиотеки.

Для разработки библиотеки потребовалось бы проводить такие преобразования для
каждой функции. А кроме того, писать однотипный код обработчика. Поэтому, для
упрощения задачи был написан генератор кода, который на основе специальных
коментариев создавал бы обработчики с правильными именами.

Теперь рассмотрим, как все элементы этой системы будут взаимодействовать вместе.

#### Архитектура системы

В правой части слайда представлена схема аналогичная рассмотренной ранее.

В левой части у нас появляется сервер и приложение управления. Они нужны для
того, чтобы запускать множество приложений и отображать палитру команд.

Внедренная библиотека сообщает серверу обо всех появившихся элеменитах. Сервер
передает эту информацию приложению управления для отображения палитры команд.
Когда пользователь выбрал команду, вызывается функция сервера.

Сервер, в свою очередь передает эту команду библиотеке. Но библиотека не может
быть инициатором действия, т.к. управление находится во внутренностях Qt.
Поэтому оно должно как-то получить инициативу. Для этого сервер посылает
графической подсистеме команду активации окна. Х11 передает это событие
библиотеке Qt, а она, в свою очередь вызывает функцию приложения для обработки
событий. В этот момент вызов перехватывается внедренным модулем и производится
активация нужного элемента. Ну и конечно передается штатное событие.

#### Протокол

Для общения библиотеки с сервером используется командный протокол.

Команды представляют собой строку, в начале которой передается её длина и
фиксированный набор параметров для каждой известной команды.

Всего доступно 6 команд:
* сообщение о запуске нового приложения. Его посылает библиотека серверу при
вызове первой функции.
* оповещение об установке текста элемента. Также используется, когда элемент
только создан.
* удаление элемента
* сообщение о том, что окно было активировано
* привязка элемента к окну
* и команда активации.

#### Интерфейс

Сервер является частью приложения управления, которая предоставляет
пользовательский интерфейс для работы. Само приложение отображается иконкой на
панели оповещений. В её контекстном меню есть три пункта: отображение палитры
команд, запуск нового приложения и закрытие.

Т.к. использовать контекстное меню каждый раз неудобно, к действиям были
привязаны грячие клавиши, которые перехватываются в любом окне.

#### Интерфейс (2)

Для отображения палитры команд и выбора приложения используется один и тот же
интерфейс. Это меню rofi которое отображает список элементов и поддерживает
возможность нечеткого поиска. Т.е. пользователь может ввести любую часть команды
или даже несколько частей для поиска.

#### Заключение

В результате работы была реализована библиотека для перехвата событий,
вспомгательный генератор кода для её разработки и расширения. А также приложение
управления, которое позволяет запускать приложения и отображать в них палитру
команд.