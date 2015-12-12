# 主な使い方
公開鍵の作成、設置を少し楽にするツールを作りました。
# 初めに

Unix系のSSH公開鍵認証鍵の作成と設置ってやることは単純で、ほぼやることは同じだけど、地味に面倒いですよね。

これを可能な限り自動化したいなというのがきっかけです。

概ねやることはこんな感じだと思います。


```
# (1) 鍵作成　
ssh-keygen -N "" -t rsa -f ~/.ssh/id_rsa

# (2-a) 鍵をサーバーに転送する
ssh-copy-id -i /~/.ssh/id_rsa.pub hoge@sample.com

# (2-b)もしくは手動でサーバーのauthorized_keysに追記する
cat ~/.ssh/id_rsa.pub| ssh hoge@sample.com "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && chmod 700 ~/.ssh/ && chmod 755 ~/"

# (3) 必要なら秘密鍵情報を追記する
vi ~/.ssh/config
```

毎日使うわけじゃないけど
対象のサーバーがたくさんあると地味に面倒だし、
自動化出来そうなんだよなぁ。と思ったのがきっかけです。
　
## 免責事項
秘密鍵を扱うので
動作原理が理解できる方のみご使用ください。


# 使い方
```
python pubkey.py
#もしくは実行権限をつけて
./pubkey.py
```
```ヘルプ
./pubkey.py -h
usage: pubkey.py [-h] [-l] [-p PrivateKeyPath] [-k] [-c] [-a ALIAS]
                 [-N PassPhrase]
                 server
positional arguments:
  server                user@server

optional arguments:
  -h, --help            show this help message and exit
  -l, --LocalOnly       オプションをつけると、サーバー上の操
                        作を行いません。
  -p PrivateKeyPath, --private PrivateKeyPath
                        private key のパスです [default
                        /Users/ono/.ssh/id_rsa]
  -k, --keygen          keygenで鍵を生成します
  -c, --config          .ssh/config にHost情報を書き込みます
  -a ALIAS, --alias ALIAS
                        -cオプションをつけた時のみ有効,
                        configファイルの
                        Host欄をこの指定にします
  -N PassPhrase         パスフレーズを指定します。空文字も可
                        能です。(-k オプション時に有効です）
```

## リモート上に鍵を追記する

最低限のコマンド

```
./pubkey.py hoge@sample.com
```

~/.ssh/id_rsa.pubを公開鍵として
hoge@sample.com の~/.ssh/authorized_keys に公開鍵を追記します。
この時、ローカルで`ssh-copy-id`コマンドが利用できるなら　(2-a)を利用し、利用できないのなら、(2-b)を実行します。

もちろんサーバーのパスワードを入力してください。


## 秘密鍵と公開鍵の生成もする(-k)

```
./pubkey.py -k hoge@sample.com
```

(2)を実行するまえに(1)を実行します。
この時、単純に(1)を呼び出してるので、表示に従ってパスフレーズを入力してください。

## パスフレーズを指定する(-N)

```
./pubkey.py -N "" -k hoge@sample.com
```


(1)の呼び出し時、パスフレーズを打つのがめんどい方用です。
ssh-keygen 呼び出し時に -Nオプションをつけています。

## 秘密鍵ファイルを指定する。(-p/--private)
```
./pubkey.py -p ~/.ssh/key -N "" -k hoge@sample.com
./pubkey.py --private ~/.ssh/key -N "" -k hoge@sample.com
```

デフォルトの秘密鍵以外を使いたい場合です。
-pの後に秘密鍵のパスを指定してください。
公開鍵は~/.ssh/key.pub　のように.pubが付加されるものが使われます。

## ~/.ssh/config　にデータを書く (-c)
```
./pubkey.py -c -p ~/.ssh/key -N "" -k hoge@sample.com
```

-cオプションをつけると~/.ssh/configに下のようなテキストが追記されます。
(3)の処理の自動化

```
Host sample.com
       User hoge
       IdentityFile ~/.ssh/key
```


### aliasを指定します。(-a)
```
./pubkey.py -a sample -c -p ~/.ssh/key -N "" -k hoge@sample.com
```
簡単にいうと下のように追記されます。

```
Host sample
		hostname sample.com
       User hoge
       IdentityFile ~/.ssh/key
```

これを設定すると、このように下のように接続できます。
（ユーザー名とhostnameの省略）

```
ssh sample
```


## リモート上に公開鍵を置く処理をしない(-l/--LocalOnly)
```
./pubkey.py -l -a sample -c -p ~/.ssh/key -N "" -k hoge@sample.com
```

 (2)を実行しません。
 keygenやconfigファイルは作りたいけど、リモート上に公開鍵を置く必要が無い場合に指定します。
 主にデバッグ用です。





# unit test

python test_pubkey.py