package org.tcchou.groovy;

import groovy.util.BuilderSupport;
import groovy.lang.GroovyShell;
import groovy.lang.GString;

import java.util.*;
import java.io.OutputStream;
import java.io.IOException;
import java.math.BigDecimal;

//import org.apache.poi.hssf.usermodel.*;
import org.codehaus.groovy.control.CompilationFailedException;
import org.codehaus.groovy.runtime.InvokerHelper;

import org.apache.avro.Protocol;
import org.apache.avro.generic.GenericData;
import org.apache.avro.util.Utf8;

/**
 * Using Groovy Builder and GenericData of Avro to generate Avro data.
 *
 * Pre-Req. Groovy & Avro Libraries
 *
 * User: tcchou@tcchou.org
 * Date: 2010/8/25
 */
public class AvroGroovyBuilder extends BuilderSupport {
    int level = -1;
    Protocol proto = null;
    Protocol.Message m_msg = null;
    GenericData.Record m_params = null;
    String m_curr_name = null;

    static class Node {
        int level;
        Object data;
        public Node(int level, Object data) {
            this.level = level;
            this.data = data;
        }
        
        public int getLevel() { return level; }
        public Object getData() { return data; }
    }

    public AvroGroovyBuilder(Protocol proto) {
        this.proto = proto;
    }
    
    private Object convData(Object original) {
        if (original instanceof String) {
            return new Utf8((String)original);
        } else if (original instanceof GString) {
            return new Utf8(original.toString());
        } else {
            return original;
        }
    }
    
    protected void setParent(Object parent, Object child) {
        // System.out.println("setParent(${level})");
        if (parent instanceof Node) {
            // System.out.println("\tParent Level: "+((Node)parent).level);
            level = ((Node)parent).level + 1; // adjust level
            ((Node)child).level = level;
            if ( ((Node)parent).getData() instanceof GenericData.Record &&
                    !( ((Node)child).getData() instanceof GenericData.Record ) ) {
                GenericData.Record _data = (GenericData.Record)((Node)parent).getData();
                _data.put(m_curr_name, convData(((Node)child).getData()));
            }
            // System.out.println("\tChange Level(${level})");
        }
    }

    protected Object createNode(Object name) {
        // System.out.println("createNode1: "+name);
        return createNode(name, null, null);
    }

    protected Object createNode(Object name, Object value) {
        // System.out.println("createNode2a: "+name);
        return createNode(name, null, value);
    }

    protected Object createNode(Object name, Map attributes) {
        // System.out.println("createNode2b: "+name);
        return createNode(name, attributes, null);
    }

    protected Object createNode(Object name, Map attributes, Object value) {
        level++;
        Object _name = name==null?m_curr_name:name;
        // System.out.println("createNode3(${level}): "+_name);
        Object ret = null;
        switch (level) {
        case 0:
            m_msg = proto.getMessages().get(_name);
            ret = new Node(level, m_msg);
            break;
        case 1:
            if (_name.equals("request")) {
                if (m_msg.getRequest()!=null) {
                    m_params = new GenericData.Record(m_msg.getRequest());
                    ret = new Node(level, m_params);
                }
            }
            break;
        default:
            String _type = null;
            if (attributes!=null && attributes.containsKey("type")) {
                _type = (String)attributes.get("type");
                attributes.remove("type");
            } else {
                _type = (String)_name;
            }
            if (_type!=null && proto.getType(_type)==null) {
                if (_type.length()==1) _type = _type.toUpperCase();
                else _type = _type.substring(0,1).toUpperCase() + _type.substring(1);
                if (proto.getType(_type)==null) _type=null;
            }
            // println "\ttype: ${_type}"
            GenericData.Record _data = null;
            
            if (_type!=null) {
                _data = new GenericData.Record(proto.getType(_type));
                ret = new Node(level, _data);
            } else {
                ret = new Node(level, value);
            }
            if (_data!=null && attributes!=null) {
                for (Object o : attributes.entrySet()) {
                    Map.Entry e = (Map.Entry)o;
                    _data.put((String)(e.getKey()), convData(e.getValue()));
                }
            }
            if (_type!=null) {
                m_params.put((String)_name, ((Node)ret).getData());
            }
            break;
        }
        return ret;
    }

    protected Object getName(String methodName) {
        // System.out.println("getName: "+methodName);
        m_curr_name = methodName;
        return null;
    }
    
    public GenericData.Record getParams() {
        level = -1;
        return m_params;
    }

    public static void main(String[] args) {
        GroovyShell shell = new GroovyShell();

        String script_str1 = "import org.tcchou.groovy.AvroGroovyBuilder;\n" +
            "import org.apache.avro.Protocol;\n" +
            "def proto = Protocol.parse(new File('src/main/avro/mail.avpr'));\n" +
            "def bld = new AvroGroovyBuilder(proto);\n" +
            "bld.send { request {\n" +
            "    message(to:'wei', from:'tcc', body:'foo')\n" +
            "} } \n" +
            "println bld.params \n" ;
        String script_str2 = "import org.tcchou.groovy.AvroGroovyBuilder;\n" +
            "import org.apache.avro.Protocol;\n" +
            "def proto = Protocol.parse(new File('src/main/avro/mail.avpr'));\n" +
            "def bld = new AvroGroovyBuilder(proto);\n" +
            "def zz = '123'\n"+
            "bld.send { request {\n" +
            "    message {\n" +
            "        to(\"${zz}\")\n" +
            "        from('tcc')\n" +
            "        body('foo1')\n" +
            "    }\n" +
//            "    message(to:'wei', from:'tcc', body:'foo2')\n" +
            "} } \n" +
            "println bld.params \n" ;

        try {
            Object ret = shell.evaluate(script_str2);
        } catch (CompilationFailedException e) {
            e.printStackTrace();
        }
    }
}
