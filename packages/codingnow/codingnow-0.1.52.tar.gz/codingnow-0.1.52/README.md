# codingnow_py
# CodingNow

CodingNow

pip install setuptools wheel twine

# build
python setup.py sdist bdist_wheel

# upload
twine upload dist/*
twine upload --verbose dist/*

# update
pip install codingnow --upgrade


# API token Register
pip install keyring
keyring set https://upload.pypi.org/legacy/ __token__
input api key


#24.09.11 version='0.1.5'
add background
add level control

#24.09.12 version='0.1.6'
add draw mouse position
add effect for game-over

#24.09.12 version='0.1.7'
bug fix gameover

#24.09.23 version='0.1.8'
x,y mouse position clipboard

#24.09.24 version='0.1.9'
add mouse left-click (x,y mouse position clipboard)
add weapon

#24.09.26 version='0.1.10'
add led control learning

#24.09.26 version='0.1.11'
add image player-level
add change jump value


#24.10.02 version='0.1.12'
add pip auto install


#24.10.04 version='0.1.13'
add up using left, right

#24.10.04 version='0.1.14'
Add background per level

#24.10.11 version='0.1.15'
change led ctrl 

#24.10.11 version='0.1.16'
change led ctrl (key)

#24.10.11 version='0.1.17'
modify img load delay (platfomr)

#24.10.11 version='0.1.18'
disable debug-print

#24.10.11 version='0.1.19'
monster move

#24.10.11 version='0.1.20'
monster move
#24.10.11 version='0.1.21'
add hp

#25.06.16 version='0.1.28'
map jump

#25.06.20 version='0.1.29'
If there's no life, reset the map


#25.06.27 version='0.1.30'
Add resize function (monster, exit door)

#25.06.30 version='0.1.31'
Adding Monster's Weapons and Hp

#25.06.30 version='0.1.32'
Jump per player level, set speed 

#25.06.30 version='0.1.33'
add dummy player

#25.06.31 version='0.1.34'
some change game space-war

#25.06.31 version='0.1.35'
set resouce folder path

#25.07.11 version='0.1.36'
add utils/mousepointer

#25.07.11 version='0.1.38'
add utils/mousepointer hide


#25.07.11 version='0.1.39'
add teleport

#25.07.11 version='0.1.39'
add teleport

#25.07.11 version='0.1.40'
add background alaph
#25.07.25 version='0.1.41'
time text


#26.01.12 version='0.1.42'
code examination