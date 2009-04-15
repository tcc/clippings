# -*- coding: UTF-8 -*-
#
# Copyright 2009 T.C. Chou, All rights reserved.
#
# converting OO3 to fit html block of blogger
#
#
# Copyright 2008 Omni Development, Inc.  All rights reserved.
#
# Omni Source Code software is available from the Omni Group on their
# web site at www.omnigroup.com.
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# Any original copyright notices and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# $Header: svn+ssh://source.omnigroup.com/Source/svn/Omni/trunk/Staff/wvh/Helpify/OOhelpify.py 106832 2008-11-15 02:21:21Z wvh $

# informally-assigned version number: 1.2

import sys, os, shutil, re, commands, codecs
from xml.dom.minidom import parseString

reload(sys)
sys.setdefaultencoding('utf-8')

TEXT_NODE = 3
IMAGE_PATH = "" # "HelpImages/"
COMPANY_URL = "www.example.com"

bookTitle = ""
attachments = {}
links = []
anchors = []
doNavi = True
outputPath = ""

tab_spc = 4
styles = []
styles_level_start = 2
span_levels = ['font-size: 180%']
pre_style = "background-color: #EEEEEE; border: #444444 1px solid; font-size: 80%"

def scrubAnchor(text):
    anchor = re.sub('<span class="Drop">.*?</span>', '', text)
    anchor = re.sub('\&.*?\;', '', anchor)
    anchor = re.sub('<.*?>', '', anchor)
    anchor = re.sub('\W', '', anchor)
    return anchor

def fileHeader(tehFile, title, robots="", isTop=False, url="", description=""):
    """Print to a file the stuff we need at the top of an HTML document."""

    title = re.sub('<.*?>', '', title).strip()
    
    topString = ""
    if isTop:
        topString = """<meta name="AppleTitle" content="%(title)s">
        """ % {
        'title': title
        }
    
    print >> tehFile, """<html>

    <head>
        <meta http-equiv="content-type" content="text/html;charset=utf-8">
		<title>%(title)s</title>
		%(topString)s
		%(robots)s
		<meta name="description" content="%(description)s">
        <link rel="stylesheet" href="help.css" type="text/css">
    </head>
    <body>""" % {
    'title': title,
    'topString': topString,
    'robots': robots,
    'description': description
    }


def fileFooter(tehFile):
    """Print to a file the stuff we need at the bottom of an HTML document."""
    print >> tehFile, """
    </body>
</html>"""


def fileFrames(tehFile, title, anchor):
    """Write to a file the frameset to hold a table of contents."""
    print >> tehFile, """<html>

    <head>
        <meta http-equiv="content-type" content="text/html;charset=utf-8">
        <meta name="robots" content="noindex">
        <title>%(title)s</title>
        <link href="help.css" rel="stylesheet" media="all">
    </head>

    <frameset cols="170,*">
        <frame name="left" noresize src="%(anchor)s.html">
        <frame name="right" noresize src="empty.html">
        <noframes>

            No frames.

        </noframes>
    </frameset>

</html>
    """ % {
    'title': title,
    'anchor': anchor
    }

def digItem(tehItem, level, inheritedStyle=[], destReached=False):
    
    output = ''
    applicableStyles = []
    divStyles = []
    
    itemStyles = findStyles(tehItem)
    while len(itemStyles) < 2:
        itemStyles.append([])
    if itemStyles[0]: applicableStyles.extend(itemStyles[0])
    if inheritedStyle: applicableStyles.extend(inheritedStyle) 
    
    possibleDivStyles = ['Pro', 'Box', 'Destination', 'Anchor', 'Pre']
    for oneStyle in possibleDivStyles:
        if oneStyle in applicableStyles:
            divStyles.append(oneStyle)
            applicableStyles.remove(oneStyle)
    
    #if not len(applicableStyles): applicableStyles = ['plain']
    #print applicableStyles
    
    preness = None
    if 'Pre' in divStyles:
        preness = 'Pre'
    
    text = itemText(tehItem, preness)
    anchor = ""
    
    if destReached:         #we're already at the destination; we're just filling in the text of the page.
    
        if 'Anchor' in divStyles:

            output += """<a name="%s"></a>""" % (scrubAnchor(itemText(tehItem)).lower())
            if scrubAnchor(itemText(tehItem)).lower() not in anchors:
                anchors.append(scrubAnchor(itemText(tehItem)).lower())
                    
        else:
            output += "        " + "    "*level + '<div class="item %s">' % (' '.join(divStyles))
            if text:
                output += '<span class="%(classes)s">%(text)s</span>' % {
                    'classes': ' '.join(applicableStyles),
                    'text': text
                    }
            
            for childrenNode in findSubNodes(tehItem, 'children'):
                for itemNode in findSubNodes(childrenNode, 'item'):
                    subText = digItem(itemNode, level+1, itemStyles[1], destReached=True)
                    output += subText['text']
                    
            output += "        " + "    "*level + "</div>\n"
            
        if 'Pre' in divStyles:
            output = "<pre>" + output + "</pre>"
            
        text = output       #send back all of the text of the contained nodes, formatted properly
    
    else:                   #we're not at the destination yet; we need to make a sub-page for this item.
        
        anchor = scrubAnchor(text)
        
        
        
        if "Destination" in divStyles:
            destReached = True
        
        newFileName = anchor + '.html'
        level2File = open(outputPath + '/' + newFileName, 'w')
        roboString = """<meta name="robots" content="noindex">"""
        
        if destReached:
            roboString = ""
        elif level == 2:
            divStyles.append("toc-left")
        else:
            divStyles.append("toc-right")
        
        abstract = ""
        # turn the note into an abstract; suppress this if your notes are still notes :D
        for noteNode in findSubNodes(tehItem, 'note'):
            for textNode in findSubNodes(noteNode, 'text'):
                for pNode in findSubNodes(textNode, 'p'):
                    for runNode in findSubNodes(pNode, 'run'):
                        for litNode in findSubNodes(runNode, 'lit'):
                            abstract += litNode.toxml('utf-8')
        abstract = re.sub('<.*?>', '', abstract).strip()
            
        fileHeader(level2File, text, roboString, isTop=False, url=newFileName, description=abstract)
        
        print >> level2File, """
        <div class="%(classes)s">
        <h2>%(text)s</h2>
        """ % {
        'classes': ' '.join(divStyles),
        'text': text
        }
        
        subTextList = []        # time to look at all the children of this node
        
        for childrenNode in findSubNodes(tehItem, 'children'):
            for itemNode in findSubNodes(childrenNode, 'item'):
                subTextList.append(digItem(itemNode, level+1, itemStyles[1], destReached))
        
        #print subTextList
        
        if destReached:
            for subText in subTextList:
                print >> level2File, subText['text']
        else:
            for subText in subTextList:
                target = "_top"
                #if level >= 2 and not subText['destination']:
                #    target = "right"
                frameness = ''
                print >> level2File, '<p><a href="%(anchor)s.html" target="%(target)s">%(text)s</a></p>' % {
                    'anchor': subText['anchor'] + frameness,
                    'target': target,
                    'text': subText['text']
                    }
        print >> level2File, """
        </div>
        """
        
        #make a navi thingy; suppress this stuff if you are going to index, then emit the help again with the links in it
        
        if doNavi:
            prevAnchor = ""
            prevTitle = ""
            if tehItem.previousSibling and tehItem.previousSibling.previousSibling:
                prevTitle = itemText(tehItem.previousSibling.previousSibling)
                prevAnchor = scrubAnchor(prevTitle)
            nextAnchor = ""
            nextTitle = ""
            if tehItem.nextSibling and tehItem.nextSibling.nextSibling:
                nextTitle = itemText(tehItem.nextSibling.nextSibling)
                nextAnchor = scrubAnchor(nextTitle)
            
            print >> level2File, """
        <div class="bottom-nav">
        """
            
            if prevAnchor:
                print >> level2File, """
                <span class="left-nav"><a href="%(anchor)s.html">← %(title)s</a></span>
            """ % {
                'anchor': prevAnchor,
                'title': prevTitle
                }
            
            if nextAnchor:
                print >> level2File, """
                <span class="right-nav"><a href="%(anchor)s.html">%(title)s →</a></span>
            """ % {
                'anchor': nextAnchor,
                'title': nextTitle
                }
                
            #  <a href="top.html">Top ↑</a>      
            print >> level2File, """
            &nbsp;<br/>&nbsp;
        </div>
        """
        
        #end navi thingy
        
        fileFooter(level2File)
    
    result = {}
    result['anchor'] = anchor
    result['text'] = text
    result['destination'] = destReached
    return result
        

def findSubNodes(tehParent, kind):              # get all child nodes with certain tagName
    foundNodes = []
    for subNode in tehParent.childNodes:
        if (subNode.nodeType != TEXT_NODE) and (subNode.tagName == kind):
            foundNodes.append(subNode)
    return foundNodes


def itemText(tehItem, style=None):              # find out the text of an item and send it back nicely formatted for html and css
    constructedText = u''
    for valuesNode in findSubNodes(tehItem, 'values'):
        for textNode in findSubNodes(valuesNode, 'text'):
            for pNode in findSubNodes(textNode, 'p'):
                for runNode in findSubNodes(pNode, 'run'):
                    runStyles = []
                    linkage = False
                    for styleNode in findSubNodes(runNode, 'style'):
                        for inheritedStyleNode in findSubNodes(styleNode, 'inherited-style'):
                            runStyles.append(inheritedStyleNode.getAttribute('name'))
                        if "Link" in runStyles:
                            runStyles.remove("Link")
                            linkage = True
                        if runStyles:
                            constructedText += '<span class="%s">' % (" ".join(runStyles))
                    for litNode in findSubNodes(runNode, 'lit'):
                        for leaf in litNode.childNodes:
                            leafText = evaluateLeaf(leaf)
                            if linkage:
                                constructedText += """<a href="help:anchor='%(anchor)s' bookID='%(bookTitle)s'">%(text)s</a>""" % {
                                    'anchor': scrubAnchor(leafText).lower(),
                                    'bookTitle': bookTitle,
                                    'text': leafText
                                    }
                                if scrubAnchor(leafText).lower() not in links:
                                    links.append(scrubAnchor(leafText).lower())
                            else:
                                constructedText += leafText
                    if runStyles:
                        constructedText += '</span>'
                if style == 'Pre':
                    constructedText += '\n'
    return constructedText


def evaluateLeaf(tehElement):           # find out if an element is text or attachment and send back the appropriate html
    if (tehElement.nodeType == TEXT_NODE):
        htmlText = unicode(tehElement.toxml())
        htmlText = re.sub("""“""", "&ldquo;", htmlText)
        htmlText = re.sub("""”""", "&rdquo;", htmlText)
        htmlText = re.sub("""‘""", "&lsquo;", htmlText)
        htmlText = re.sub("""’""", "&rsquo;", htmlText)
        return htmlText
    elif (tehElement.tagName == 'cell'):
        if tehElement.getAttribute('href'):
            return '<a href="%(href)s">%(name)s</a>' % {
                'href': tehElement.getAttribute('href'),
                'name': tehElement.getAttribute('name')
                }
        else:
            fileName = attachments[tehElement.getAttribute('refid')]
            fileName = re.sub("\d*__\S*?__", "", fileName)
            extension = fileName.split('.')[-1].lower()
            if extension == 'png' or extension == 'jpg' or extension == 'gif':
                return '<img src="%s" class="inline-image">' % (IMAGE_PATH + fileName)
            else:
                return '<a href="%(fileName)s">%(name)s</a>' % {
                    'fileName': fileName,
                    'name': tehElement.getAttribute('name')
                    }


def findStyles(tehElement):
    """returns list of lists; inside list represents styles; outside list represents stack levels"""
    itemStyles = []
    for styleNode in findSubNodes(tehElement, 'style'):
        nextStyle = []
        for inheritedStyleNode in findSubNodes(styleNode, 'inherited-style'):
            nextStyle.append(inheritedStyleNode.getAttribute('name'))
        itemStyles.append(nextStyle)
    return itemStyles
    
def findStyleValues(styleNode):
    styleValues = {}
    for styleVal in findSubNodes(styleNode, 'value'):
        kk = styleVal.getAttribute('key')
        vv=''
        for leaf in styleVal.childNodes:
            evv = evaluateLeaf(leaf)
            if evv and evv.strip(): vv += evv
        styleValues[kk] = vv
        # print "    %(key)s:%(val)s" % {'key':kk, 'val':vv}
    named_styles = []
    for styleVal in findSubNodes(styleNode, 'inherited-style'):
        named_styles.append(styleVal.getAttribute('name'))
    if len(named_styles)>0: styleValues['named_styles']=named_styles

    return styleValues


def main():

    if len(sys.argv) >= 2:
    
        global outputPath
        inputPath = sys.argv[1]
        if inputPath[-1] == '/':
            inputPath = inputPath[0:-1]
        inputTitle = inputPath.split('/')[-1].split('.')[0]
        outputPath = inputPath + '/../%s/' % (inputTitle)
        if not os.access(outputPath, os.F_OK):
            os.mkdir(outputPath)
        if not os.access(outputPath + '/HelpImages', os.F_OK):
            os.mkdir(outputPath + '/HelpImages')
        
        if os.access(outputPath + '/../help.css', os.F_OK):
            shutil.copyfile(outputPath + '/../help.css', outputPath + '/help.css')
        if os.access(outputPath + '/../Icon.png', os.F_OK):
            shutil.copyfile(outputPath + '/../Icon.png', outputPath + '/HelpImages/Icon.png')

        print  inputPath+"\n"
        f = codecs.open(inputPath + '/contents.xml', 'r', 'utf-8')
        xmlString = f.read().encode('utf-8')
        tehTree = parseString(xmlString)
        f.close()
        
        docNode = tehTree.documentElement
        
        #print tehTree.documentElement.tagName
        #print tehTree.documentElement.getAttribute('crap')
        
        rootNode = None
        for oneNode in findSubNodes(docNode, 'root'):
            rootNode = oneNode
        
        style_attr_idx = 0
        for styleElem in findSubNodes(rootNode, 'style'):
            print "[%(idx)s]" % {'idx':style_attr_idx}
            ss = findStyleValues(styleElem)
            for i in ss:
                print "    %(key)s=%(val)s" % {'key':i, 'val':ss[i]}
            style_attr_idx=style_attr_idx+1
        
        for attachmentsNode in findSubNodes(docNode, 'attachments'):
            for attachmentNode in findSubNodes(attachmentsNode, 'attachment'):
                if attachmentNode.getAttribute('href'):
                    attachments[attachmentNode.getAttribute('id')] = attachmentNode.getAttribute('href')
                    if attachmentNode.getAttribute('href').find("__#$!@%!#__") == -1:       ## get rid of INSANE outliner dupe files
                        shutil.copyfile((inputPath + '/' + attachmentNode.getAttribute('href')), outputPath + (IMAGE_PATH=="" and "" or '/'+IMAGE_PATH+'/') + attachmentNode.getAttribute('href'))
        
        
        #This is where the files get generated. If we are adding navigation links, then generate the pages once without navi links for indexing, then once more with the navi links. If we are not adding navi, then just generate the pages once and index them.
        naviIterations = [False]
        if doNavi:
            naviIterations = [False, True]
        
        for oneNaviIteration in naviIterations:
            
            for oneNode in rootNode.childNodes:
                if (oneNode.nodeType != TEXT_NODE) and (oneNode.tagName == 'item'):
                    text = itemText(oneNode, 'title')
                    global bookTitle
                    bookTitle = text
                    
                    tocFile = open(outputPath + '/top.html', 'w')
                    fileHeader(tocFile, bookTitle, """<meta name="robots" content="noindex">""", isTop=True, url='top.html')
                    
                    print >> tocFile, """
                        <div class="top-all">
                            <div class="top-left">
                                <img src="%(imagePath)sIcon.png" alt="Application Icon" height="128" width="128" border="0">
                                <h1>%(bookTitle)s</h1>
                                <p><a href="http://%(url)s">%(url)s</a></p>
                            </div>
                            <div class="top-right">
                    """ % {
                        'imagePath': IMAGE_PATH,
                        'bookTitle': bookTitle,
                        'url': COMPANY_URL
                        }
                    
                    for childrenNode in findSubNodes(oneNode, 'children'):
                        for itemNode in findSubNodes(childrenNode, 'item'):
                            subText = digItem(itemNode, 2, [])
                            frameness = ''
                            #if not subText['destination']:
                            #    frameFile = open(outputPath + '/' + subText['anchor'] + 'frame.html', 'w')
                            #    fileFrames(frameFile, subText['text'], subText['anchor'])
                            #    frameness = 'frame'
                            print >> tocFile, '<p><a href="%(anchor)s.html">%(text)s</a></p>' % {
                                'anchor': subText['anchor'] + frameness,
                                'text': subText['text']
                                }
                    
                    print >> tocFile, """
                            </div>
                        </div>
                    """
                    
                    fileFooter(tocFile)
                    tocFile.close()
                
            # create a help index on the iteration that has no navi
            #if not oneNaviIteration:
            #    print commands.getoutput("""/Developer/Applications/Utilities/Help\ Indexer.app/Contents/MacOS/Help\ Indexer %s""" % (outputPath.replace(' ', '\ ')))
        
        # check that all links are hooked up
        links.sort()
        anchors.sort()
        
        anchorlessLinks = []
        for oneLink in links:
            if oneLink not in anchors:
                anchorlessLinks.append(oneLink)
        
        if len(anchorlessLinks):
            print "\n_______Anchorless Links_______"
            for oneLink in anchorlessLinks:
                print oneLink
                
            #print "\n_______All Links______________"
            #for oneLink in links:
            #    print oneLink
            #
            #print "\n_______All Anchors____________"
            #for oneAnchor in anchors:
            #    print oneAnchor
            
            print "\n"
                
        else:
            print "Congratulations, all links are hooked up!"
    
    else:
        print """usage: 
    python OOhelpify.py OutlinerFile.oo3"""

def findHeadingType(style):
    if style is not None and style.has_key(u'heading-type(com.omnigroup.OmniOutliner)'):
        return str(style[u'heading-type(com.omnigroup.OmniOutliner)'])
    return 'default'

def hasGrandChild(tehItem):
    grandchild = False
    for childrenNode in findSubNodes(tehItem, 'children'):
        for itemNode in findSubNodes(childrenNode, 'item'):
            gchild = findSubNodes(itemNode, 'children')
            if gchild and len(gchild)>0:
                grandchild = True
                break
        if grandchild: break
    return grandchild

def digItem2(tehFile, tehItem, level, passed_style=None):
    items = 0
    grandchild = hasGrandChild(tehItem)
    #print "Grandchild: "+str(grandchild)
    for childrenNode in findSubNodes(tehItem, 'children'):
        text = ''
        level_style = None
        if level+styles_level_start < len(styles): level_style = styles[level+styles_level_start]
        passed_heading = findHeadingType(passed_style)
        level_heading = findHeadingType(level_style)
        parent_heading = 'None'
        if passed_heading!='default': parent_heading=passed_heading
        elif level_heading!='default': parent_heading=level_heading
        # print " "*level+'parent heading: '+str(parent_heading)
        itemStyles = findStyles(tehItem)        
        parent_preness = None
        for preItemStyles in itemStyles:
            if u'Pre' in preItemStyles: parent_preness = 'Pre'
        
        span_level = None
        if level+1 <= len(span_levels): span_level = span_levels[level]
        spc = " "*tab_spc*(level-len(span_levels))
        pairs = []
        for itemNode in findSubNodes(childrenNode, 'item'):
            curr_style = None
            child_style = None
            style_idx = 0

            preness = None
            itemStyles = findStyles(itemNode)
            if 'Pre' in itemStyles: preness = 'Pre'
            else: preness = parent_preness

            for styleElem in findSubNodes(itemNode, 'style'):
                eval_style = findStyleValues(styleElem)
                if style_idx==0: curr_style = eval_style
                elif style_idx==1: child_style = eval_style
                style_idx += 1
                if not preness and eval_style.has_key('named_styles'):
                    if 'Pre' in eval_style['named_styles']: preness = 'Pre'

            heading = findHeadingType(curr_style)
            # print "current: "+heading
            if heading=='default': heading = parent_heading


            if preness=='Pre':
                print >> tehFile, "<pre style=\"%s\">" % pre_style
                pairs.append("</pre>")
            elif not span_level:
                if items==0:
                    if heading in ['Legal','Numeric']:
                        print >> tehFile, spc+"<ol>"
                        pairs.append(spc+"</ol>")
                    elif grandchild:
                        print >> tehFile, spc+"<ul>"
                        pairs.append(spc+"</ul>")
                    else:
                        print >> tehFile, "<div>"
                        pairs.append("</div>")
                else:
                    if heading not in ['Legal','Numeric'] and not grandchild:
                        print >> tehFile, "<br/>"

            text = itemText(itemNode, preness)
            if preness=='Pre': text = text.strip()
            print text
            # print " "*level+"["+str(level)+"] "+str(heading)+": "+text
            if preness=='Pre':
                tehFile.write(spc+text.strip())
            elif span_level:
                if len(text)>0:
                    if heading in ['Legal','Numeric']:
                        print >> tehFile, spc+"""<span style="%(style)s">%(idx)s. %(text)s</span>""" % {'style':span_level, 'text':text, 'idx': items+1}
                    else:
                        print >> tehFile, spc+"""<span style="%(style)s">%(text)s</span>""" % {'style':span_level, 'text':text}
            else:
                if heading in ['Legal','Numeric'] or grandchild:
                    tehFile.write(spc+"<li>"+text.strip())
                else:
                    tehFile.write(spc+text.strip())
            childs = digItem2(tehFile, itemNode, level+1, child_style)
            if not span_level:
                if preness=='Pre':
                    pass
                elif heading in ['Legal','Numeric'] or grandchild:
                    if childs>0: print >> tehFile, spc+"</li>"
                    else: print >> tehFile, "</li>"
            items += 1
        pairs.reverse()
        for pair in pairs:
            print >> tehFile, pair
    return items        
            
def main2():
    if len(sys.argv) >= 2:
    
        global outputPath
        inputPath = sys.argv[1]
        if inputPath[-1] == '/':
            inputPath = inputPath[0:-1]
        inputTitle = inputPath.split('/')[-1].split('.')[0]
        outputPath = inputPath + '/../%s/' % (inputTitle)
        if not os.access(outputPath, os.F_OK):
            os.mkdir(outputPath)
        if not os.access(outputPath + '/HelpImages', os.F_OK):
            os.mkdir(outputPath + '/HelpImages')
        
        print  inputPath+"\n"
        f = codecs.open(inputPath + '/contents.xml', 'r', 'utf-8')
        xmlString = f.read().encode('utf-8')
        tehTree = parseString(xmlString)
        f.close()
        
        docNode = tehTree.documentElement
        
        #print tehTree.documentElement.tagName
        #print tehTree.documentElement.getAttribute('crap')


        
        rootNode = None
        for oneNode in findSubNodes(docNode, 'root'):
            rootNode = oneNode

        style_attr_idx = 0
        for styleElem in findSubNodes(rootNode, 'style'):
            print "[%(idx)s]" % {'idx':style_attr_idx}
            ss = findStyleValues(styleElem)
            styles.append(ss)
            for i in ss:
                print "    %(key)s=%(val)s" % {'key':i, 'val':ss[i]}
            style_attr_idx=style_attr_idx+1
            
        for attachmentsNode in findSubNodes(docNode, 'attachments'):
            for attachmentNode in findSubNodes(attachmentsNode, 'attachment'):
                if attachmentNode.getAttribute('href'):
                    attachments[attachmentNode.getAttribute('id')] = attachmentNode.getAttribute('href')
                    if attachmentNode.getAttribute('href').find("__#$!@%!#__") == -1:       ## get rid of INSANE outliner dupe files
                        shutil.copyfile((inputPath + '/' + attachmentNode.getAttribute('href')), outputPath + (IMAGE_PATH=="" and "" or '/'+IMAGE_PATH+'/') + attachmentNode.getAttribute('href'))

        for oneNode in rootNode.childNodes:
            if (oneNode.nodeType != TEXT_NODE) and (oneNode.tagName == 'item'):
                text = itemText(oneNode, 'title')        
                global bookTitle, outFile
                bookTitle = text
                
                outFile = open(outputPath + '/index.html', 'w')
                fileHeader(outFile, bookTitle, """<meta name="robots" content="noindex">""", isTop=True, url='top.html')

                print text                
                print '*'*50
                digItem2(outFile, oneNode, 0)

                fileFooter(outFile)
                outFile.close()
    else:
        print """usage: 
    python OOblogger.py OutlinerFile.oo3"""

if __name__ == "__main__":
    main2()