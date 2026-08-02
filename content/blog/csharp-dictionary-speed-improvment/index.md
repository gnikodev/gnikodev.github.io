+++
title = "Ускоряем работу C# Dictionary в 2 раза."
description = "Способ оптимизации работы типа Dictionary в языке программирования C#."
date = 2025-04-18
updated = 2025-04-18
draft = false
in_search_index = true

# [taxonomies]
# tags = ["dotnet","csharp","dictionary", "cs"]
# [extra]
# keywords = "DotNET, C#, Dictionary"
# giscus = true
# series = "dotnet"
+++

Давайте поговорим о том, как оптимизировать производительность типа `Dictionary` в C#.

Этот тип данных — один из самых популярных типов коллекций .NET, и его правильное использование может значительно улучшить производительность вашего приложения. Сначала рассмотрим немного теории работы словаря, а после познакомимся со способами ускорения методов вставки элементов.

## Как работает Dictionary?

Перед тем как перейти к оптимизации, давайте разберемся, как вообще работает `Dictionary`.

Словарь представляет собой реализацию стандартной хеш-таблицы. Его суть работы состоит в том, чтобы однозначно связать ключ с его значением. И каждый раз когда мы делаем запрос по этому ключу, мы всегда должны получать одно и то же значение. Ключи могут быть как ссылочными, так и значимыми типами. Инициализация происходит либо при создании (если передана начальный размер коллекции), либо при добавлении первого элемента, причем в качестве размера будет выбрано ближайшее простое число. При этом создаются 2 внутренние коллекции — **int[] buckets** и **Entry[] entries**.

```cs
public class Dictionary<TKey, TValue> :
    IDictionary<TKey, TValue>,
    ICollection<KeyValuePair<TKey, TValue>>,
    IEnumerable<KeyValuePair<TKey, TValue>>,
    IEnumerable,
    IDictionary,
    ICollection,
    IReadOnlyDictionary<TKey, TValue>,
    IReadOnlyCollection<KeyValuePair<TKey, TValue>>,
    ISerializable,
    IDeserializationCallback
    where TKey : notnull
  {
    #nullable disable
    private int[] _buckets;
    private Dictionary<TKey, TValue>.Entry[] _entries;
    private ulong _fastModMultiplier;
    private int _count;
    private int _freeList;
    private int _freeCount;
    private int _version;
    private IEqualityComparer<TKey> _comparer;
    private Dictionary<TKey, TValue>.KeyCollection _keys;
    private Dictionary<TKey, TValue>.ValueCollection _values;
```

Первая будет содержать индексы элементов во второй коллекции, а она, в свою очередь, сами элементы в таком виде:

```cs
    private struct Entry
   {
     public uint hashCode;
     public int next;
     public TKey key;
     public TValue value;
   }
```

При добавлении элемента вычисляется хэшкод его ключа и затем — индекс корзины в которую он будет добавлен по модулю от величины коллекции. Затем проверяется нет ли уже такого ключа в коллекции, если есть — то операция Add выбросит исключение, а присваивание по индексу просто заменит элемент на новый.

```cs
// выбросит исключение
dictionary.Add(10, 20);

// просто подменит значение на новое
dictionary[10] = 20;
```

Если достигнут максимальный размер словаря, то происходит расширение (выбирается новый размер в 2 раза больше предыдущего, и округляется до ближайшего простого числа). Дальше старый словарь полностью копируется в новое выделенное место. А старая область памяти будет подвержена сборки мусора. Сложность такой операции будет соответственно — O(n).

Если происходит коллизия (в корзине индексов `_buckets` уже есть элемент), то новый элемент добавляется в коллекцию, его индекс сохраняется в корзине, а индекс старого элемента — в его поле next.

![Пример работы с колизией](./images/image_1.png)

В результате мы получаем односвязный список относительно дублируемого ключа хеширования. Данный механизм разрешения коллизий называется **chaining**. Чтобы предотвратить такое поведение, необходимо выбирать такой алгоритм в методе `GetHashCode`, который будет давать максимально уникальные значения.

## Проблема двойного хеширования

Предположим, необходимо выполнить вставку в словарь какого-либо значения, но перед этим проверить, если ключ уже существует, то вернуть то значение которое уже было записано:

```cs
if (!dictionary.ContainsKey(key))
{
    dictionary[key] = value;
}
```

На первый взгляд, это кажется логичным решением. Но проблема заключается в том, что здесь происходит **двойное хеширование**:

1. При вызове `ContainsKey` вычисляется хеш для проверки существования ключа.
2. При добавлении элемента снова вычисляется хеш.

Это приводит к дополнительной нагрузке, особенно если такая операция выполняется в цикле или в горячих путях программы.

## Решение проблемы через TryGetValue

Одним из способов минимизировать эту проблему является использование метода `TryGetValue`:

```cs
if (!dictionary.TryGetValue(key, out _))
{
    dictionary[key] = value;
}
```

Этот подход позволяет избежать явного вызова `ContainsKey`, но все равно требует двух обращений к словарю:

1. Проверка наличия ключа.
2. Добавление значения.

Например, у класса ConcurrentDictionary есть метод GetOrAdd, который лишен проблемы с двойным доступом к словарю.

Как можно упростить работу и сохранить функционал? Для начала можно обернуть двойной доступ в отдельный метод GetOrAdd и там разместить методы по добавлению значения. 

```cs

public static class DictionaryExtensions
{
    public static TValue GetOrAdd<TKey, TValue>(this Dictionary<TKey, TValue> dictionary, TKey key, TValue value)
        where TKey : notnull
    {
        if (!dictionary.TryGetValue(key, out existedValue))
        {
            dictionary[key] = value;
            return value;
        }       
        return existedValue;
    }

}

```

Но это не решает проблему. Мы все равно делаем две операции доступа по ключу.

Можно ли сделать лучше?

## Эффективное решение через CollectionMarshal

Да, можно! В современном .NET есть класс `System.Runtime.InteropServices.CollectionsMarshal`, который предоставляет метод `TryGetValueRefOrAddDefault`. Он позволяет получить ссылку на значение по ключу или добавить значение за одно обращение к словарю. Вот пример использования:

```cs
using System.Runtime.InteropServices;

public static TValue GetOrAdd<TKey, TValue>(this Dictionary<TKey, TValue> dictionary, TKey key, TValue defaultValue)
{
    ArgumentNullException.ThrowIfNull(dictionary);
    ref var slot = ref CollectionsMarshal.GetValueRefOrAddDefault(dictionary, key, out bool exists);
    if (exists) return slot!;

    slot = value;
    return value;
}
```

Этот метод доступен начиная с .NET 6 и выше. Он особенно полезен, когда вам нужно выполнять операции "получить или добавить" в высокопроизводительных частях кода.

## Расширение функциональности

Кроме `GetOrAdd`, вы можете реализовать другие полезные методы для словарей, например:

### TryUpdate

Метод `TryUpdate` позволяет обновить значение по ключу, если ключ уже существует:

```cs
public static bool TryUpdate<TKey, TValue>(this Dictionary<TKey, TValue> dictionary, TKey key, TValue value)
    where TKey : notnull
{
    ArgumentNullException.ThrowIfNull(dictionary);
    ref var slot = ref CollectionsMarshal.GetValueRefOrNullRef(dictionary, key);
    if (Unsafe.IsNullRef(ref slot)) return false;

    slot = value;
    return true;
}
```

Таким же образом можно создать другие методы расширения для словарей, например:

### RemoveIfExists

Позволяет удалить ключ, если он существует.

```cs
public static bool RemoveIfExists<TKey, TValue>(this Dictionary<TKey, TValue> dictionary, TKey key)
    where TKey : notnull
{
    ArgumentNullException.ThrowIfNull(dictionary);
    // Получаем ссылку на значение по ключу или null, если ключа нет
    ref var slot = ref CollectionsMarshal.GetValueRefOrNullRef(dictionary, key);

    // Если ссылка не является null, значит ключ существует
    if (Unsafe.IsNullRef(ref slot)) return false; // Ключ не существует, ничего не делаем

    dictionary.Remove(key); // Удаляем ключ
    return true; // Возвращаем true, так как ключ был удален
}
```

### Upsert

Позволяет обновить значение, если ключ существует, или добавить новое значение.

```cs
public static void Upsert<TKey, TValue>(this Dictionary<TKey, TValue> dictionary, TKey key, TValue value)
    where TKey : notnull
{
    ArgumentNullException.ThrowIfNull(dictionary);

    // Получаем ссылку на значение по ключу или default(TValue), если ключа нет
    ref var slot = ref CollectionsMarshal.GetValueRefOrAddDefault(dictionary, key, out _);

    // Если ключ существует, обновляем значение
    // Если же не существует, то добавляем значение
    slot = value;
}
```

## Практический пример

Давайте рассмотрим практический пример использования этих методов:

```cs
var dictionary = new Dictionary<int, string>();
dictionary.GetOrAdd(1, "Value1");
dictionary.TryUpdate(1, "UpdatedValue1");

Console.WriteLine(JsonSerializer.Serialize(dictionary)); // {"1":"UpdatedValue1"}
```

Как видите, эти методы делают работу со словарем более эффективной и чистой.

## Заключение

Подведем итоги:

- Использование `ContainsKey` и `TryGetValue` может быть неэффективным из-за двойного хеширования.
- Методы `CollectionsMarshal` позволяют оптимизировать работу со словарями.
- Создание своих методов расширения поможет сделать ваш код более удобным и производительным.

Дополнительные источники:

- [Ссылка на проект с исходным кодом](https://github.com/just-squad/just-platform-dotnet/blob/main/src/JustPlatform.Extensions/DictionaryExtensions.cs)
- [YouTube видео](https://www.youtube.com/watch?v=6CWQXQISYpk)
